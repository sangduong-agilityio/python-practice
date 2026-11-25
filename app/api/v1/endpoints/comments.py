"""
app/api/v1/endpoints/comments.py
---------------------------------
Task comment endpoints: add and list under a task, edit and delete by comment id.
"""

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.task_comment import (
    TaskCommentCreate,
    TaskCommentList,
    TaskCommentResponse,
    TaskCommentUpdate,
)
from app.services.task_comment_service import TaskCommentService

router = APIRouter(tags=["Comments"])


@router.post(
    "/tasks/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
)
async def create_comment(
    task_id: int,
    data: TaskCommentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskCommentResponse:
    """Add a comment to a task. Caller must be the project owner or task assignee."""
    service = TaskCommentService(db)
    return await service.create(task_id, data, current_user)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=TaskCommentList,
    summary="List comments on a task",
)
async def list_comments(
    task_id: int,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TaskCommentList:
    """
    List non-deleted comments on a task, oldest first.
    Caller must be the project owner or task assignee.
    """
    service = TaskCommentService(db)
    return await service.list_for_task(
        task_id, current_user, limit=limit, offset=offset
    )


@router.patch(
    "/comments/{comment_id}",
    response_model=TaskCommentResponse,
    summary="Edit your comment",
)
async def update_comment(
    comment_id: int,
    data: TaskCommentUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskCommentResponse:
    """Replace the content of a comment. Only its author can edit it."""
    service = TaskCommentService(db)
    return await service.update(comment_id, data, current_user)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """
    Remove a comment from the task (soft delete).
    Its author or the owner of the task's project can delete it.
    """
    service = TaskCommentService(db)
    await service.delete(comment_id, current_user)
