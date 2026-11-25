"""
app/services/task_comment_service.py
--------------------------------------
Business logic for task comments (docs/epics/task-comments.md).

Read and add: the owner of the task's project or the task's assignee.
Edit: the comment's author only. Delete: the author or the project owner.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.task_comment import TaskComment
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_comment_repository import TaskCommentRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task_comment import (
    TaskCommentCreate,
    TaskCommentList,
    TaskCommentResponse,
    TaskCommentUpdate,
)


class TaskCommentService:
    """Handles creating and listing comments on a task."""

    def __init__(self, db: AsyncSession) -> None:
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.comment_repo = TaskCommentRepository(db)

    async def _get_task_or_404(self, task_id: int) -> Task:
        """Fetch task by ID or raise 404."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )
        return task

    async def _check_comment_access(self, task: Task, user: User) -> None:
        """
        R1: the caller must be the owner of the task's project or the task assignee.
        """
        if task.assignee_id == user.id:
            return
        project = await self.project_repo.get_by_id(task.project_id)
        if project is not None and project.owner_id == user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access comments on this task",
        )

    async def create(
        self, task_id: int, data: TaskCommentCreate, current_user: User
    ) -> TaskCommentResponse:
        """Add a comment to a task (project owner or assignee only)."""
        task = await self._get_task_or_404(task_id)
        await self._check_comment_access(task, current_user)
        comment = await self.comment_repo.create(
            task_id=task_id, author_id=current_user.id, content=data.content
        )
        return TaskCommentResponse.model_validate(comment)

    async def list_for_task(
        self, task_id: int, current_user: User, limit: int = 20, offset: int = 0
    ) -> TaskCommentList:
        """List non-deleted comments on a task (project owner or assignee only)."""
        task = await self._get_task_or_404(task_id)
        await self._check_comment_access(task, current_user)

        comments = await self.comment_repo.list_by_task(
            task_id, limit=limit, offset=offset
        )
        total = await self.comment_repo.count_by_task(task_id)
        return TaskCommentList(
            items=[TaskCommentResponse.model_validate(c) for c in comments],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _get_comment_or_404(self, comment_id: int) -> TaskComment:
        """Fetch a visible comment or raise 404 (soft-deleted ones count as missing)."""
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment {comment_id} not found",
            )
        return comment

    async def update(
        self, comment_id: int, data: TaskCommentUpdate, current_user: User
    ) -> TaskCommentResponse:
        """Edit a comment's content (author only)."""
        comment = await self._get_comment_or_404(comment_id)
        if comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can edit this comment",
            )
        comment = await self.comment_repo.update_content(comment, data.content)
        return TaskCommentResponse.model_validate(comment)

    async def delete(self, comment_id: int, current_user: User) -> None:
        """Soft-delete a comment (its author or the owner of the task's project)."""
        comment = await self._get_comment_or_404(comment_id)
        if comment.author_id != current_user.id:
            task = await self._get_task_or_404(comment.task_id)
            project = await self.project_repo.get_by_id(task.project_id)
            if project is None or project.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the author or the project owner can delete this comment",
                )
        await self.comment_repo.soft_delete(comment)
