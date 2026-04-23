"""
Task business logic.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidFieldException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.core.websocket import manager
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import (
    TaskAssignUpdate,
    TaskCreate,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.worker.tasks import send_task_assigned_email

log = structlog.get_logger(__name__)


class TaskService:
    """Handles task-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)
        self.tag_repo = TagRepository(db)

    async def get_or_404(self, task_id: int) -> Task:
        """Fetch a task by ID or raise a ResourceNotFoundException if not found."""
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise ResourceNotFoundException("Task")
        return task

    async def assert_project_access(self, task: Task, user: User) -> None:
        """Assert that ``user`` can access ``task`` via its parent project."""
        project = await self.project_repo.get_by_id(task.project_id)
        if project is None:
            raise ResourceNotFoundException("Project")

        if project.owner_id != user.id:
            raise PermissionDeniedException(
                "You do not have permission to access this resource")

    async def create(self, project_id: int, data: TaskCreate, current_user: User) -> Task:
        """Create a new task under a specific project."""
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ResourceNotFoundException("Project")

        if project.owner_id != current_user.id:
            raise PermissionDeniedException(
                "You do not have permission to access this resource")

        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            project_id=project.id,
        )
        return await self.repo.create(task)

    async def list_for_project(
        self,
        project_id: int,
        current_user: User,
        status_filter: TaskStatus | None = None,
        priority_filter: TaskPriority | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Task]:
        """Retrieve a paginated list of tasks for a project."""
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ResourceNotFoundException("Project")

        if project.owner_id != current_user.id:
            raise PermissionDeniedException(
                "You do not have permission to access this resource")

        return await self.repo.get_by_project(
            project_id=project.id,
            status=status_filter,
            priority=priority_filter,
            skip=skip,
            limit=limit,
        )

    async def update(self, task_id: int, data: TaskUpdate, current_user: User) -> Task:
        """Update general fields of a task."""
        task = await self.get_or_404(task_id)
        await self.assert_project_access(task, current_user)

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return task

        try:
            return await self.repo.update(task, updates)
        except ValueError as e:
            raise InvalidFieldException(
                str(e).replace("Cannot update field: ", "")) from e

    async def change_status(self, task_id: int, data: TaskStatusUpdate, current_user: User) -> Task:
        """Change only the status field of a task."""
        task = await self.get_or_404(task_id)
        await self.assert_project_access(task, current_user)
        return await self.repo.update(task, {"status": data.status})

    async def assign(self, task_id: int, data: TaskAssignUpdate, current_user: User, request_id: str = "unknown") -> Task:
        """Assign or unassign a user to a task."""
        task = await self.get_or_404(task_id)
        await self.assert_project_access(task, current_user)

        if data.assignee_id is not None:
            assignee = await self.user_repo.get_by_id(data.assignee_id)
            if assignee is None:
                raise ResourceNotFoundException("User")

            # Fire-and-forget via Celery
            email_task = send_task_assigned_email.delay(
                assignee.email,
                task.title,
                current_user.username,
                request_id,
            )
            log.info(
                "background_task_dispatched",
                task_name="send_task_assigned_email",
                task_id=email_task.id,
                task_title=task.title,
                assignee_id=assignee.id,
                assignee_email=assignee.email,
                assigner=current_user.username,
                request_id=request_id,
            )

            # Dispatch real-time notification via WebSocket
            await manager.send_personal_message(
                {
                    "event": "task_assigned",
                    "task_id": task.id,
                    "task_title": task.title,
                    "assigner": current_user.username,
                },
                assignee.id
            )

        return await self.repo.update(task, {"assignee_id": data.assignee_id})

    async def delete(self, task_id: int, current_user: User) -> None:
        """Delete a task permanently."""
        task = await self.get_or_404(task_id)
        await self.assert_project_access(task, current_user)
        await self.repo.delete(task)

    async def attach_tag(self, task_id: int, tag_id: int, current_user: User) -> Task:
        """Link a global tag to a specific task."""
        task = await self.get_or_404(task_id)
        await self.assert_project_access(task, current_user)

        tag = await self.tag_repo.get_by_id(tag_id)
        if tag is None:
            raise ResourceNotFoundException("Tag")

        return await self.repo.add_tag(task.id, tag)

    async def detach_tag(self, task_id: int, tag_id: int, current_user: User) -> Task:
        """Unlink a tag from a task."""
        task = await self.get_or_404(task_id)
        await self.assert_project_access(task, current_user)

        tag = await self.tag_repo.get_by_id(tag_id)
        if tag is None:
            raise ResourceNotFoundException("Tag")

        return await self.repo.remove_tag(task.id, tag)
