"""
app/services/task_service.py
------------------------------
Business logic for task CRUD, status changes, assignments, and tagging.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Handles all task-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.tag_repo = TagRepository(db)
        self.user_repo = UserRepository(db)

    async def _get_project_or_404(self, project_id: int) -> object:
        """Helper: fetch project or raise 404."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        return project

    async def get_or_404(self, task_id: int) -> Task:
        """Fetch task by ID or raise 404."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )
        return task

    def _check_project_access(self, project, user: User) -> None:
        """
        Verify user owns the project that contains a task.
        We restrict task mutations to the project owner.
        """
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify tasks in this project",
            )

    async def create(
        self, project_id: int, data: TaskCreate, current_user: User
    ) -> Task:
        """
        Create a task inside a project (project owner only).

        Args:
            project_id   : The project to add the task to.
            data         : Validated task data.
            current_user : Authenticated user (must be project owner).
        """
        project = await self._get_project_or_404(project_id)
        self._check_project_access(project, current_user)

        return await self.task_repo.create(
            title=data.title,
            description=data.description,
            project_id=project_id,
            priority=data.priority,
            due_date=data.due_date,
        )

    async def list_for_project(
        self,
        project_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        status_filter: TaskStatus | None = None,
        priority_filter: TaskPriority | None = None,
    ) -> list[Task]:
        """List tasks in a project (project owner only)."""
        project = await self._get_project_or_404(project_id)
        self._check_project_access(project, current_user)

        return await self.task_repo.list_by_project(
            project_id,
            skip=skip,
            limit=limit,
            status=status_filter,
            priority=priority_filter,
        )

    async def update(
        self, task_id: int, data: TaskUpdate, current_user: User
    ) -> Task:
        """Update a task (project owner only)."""
        task = await self.get_or_404(task_id)
        project = await self._get_project_or_404(task.project_id)
        self._check_project_access(project, current_user)

        updates = data.model_dump(exclude_none=True)
        if not updates:
            return task

        return await self.task_repo.update(task, **updates)

    async def delete(self, task_id: int, current_user: User) -> None:
        """Delete a task (project owner only)."""
        task = await self.get_or_404(task_id)
        project = await self._get_project_or_404(task.project_id)
        self._check_project_access(project, current_user)
        await self.task_repo.delete(task)

    async def change_status(
        self, task_id: int, new_status: TaskStatus, current_user: User
    ) -> Task:
        """Update only the status field of a task."""
        task = await self.get_or_404(task_id)
        project = await self._get_project_or_404(task.project_id)
        self._check_project_access(project, current_user)
        return await self.task_repo.update(task, status=new_status)

    async def assign(
        self, task_id: int, assignee_id: int | None, current_user: User
    ) -> Task:
        """
        Assign or unassign a task to a user.

        Args:
            task_id     : Task to update.
            assignee_id : User ID to assign, or None to unassign.
            current_user: Must be the project owner.

        Returns:
            Updated Task object.
        """
        task = await self.get_or_404(task_id)
        project = await self._get_project_or_404(task.project_id)
        self._check_project_access(project, current_user)

        if assignee_id is not None:
            # Verify the assignee actually exists
            assignee = await self.user_repo.get_by_id(assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {assignee_id} not found",
                )

        return await self.task_repo.update(task, assignee_id=assignee_id)

    async def add_tag(self, task_id: int, tag_id: int, current_user: User) -> Task:
        """Attach a tag to a task."""
        task = await self.get_or_404(task_id)
        project = await self._get_project_or_404(task.project_id)
        self._check_project_access(project, current_user)

        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found",
            )

        return await self.task_repo.add_tag(task, tag)

    async def remove_tag(self, task_id: int, tag_id: int, current_user: User) -> Task:
        """Detach a tag from a task."""
        task = await self.get_or_404(task_id)
        project = await self._get_project_or_404(task.project_id)
        self._check_project_access(project, current_user)

        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {tag_id} not found",
            )

        return await self.task_repo.remove_tag(task, tag)
