"""
app/api/v1/endpoints/comments.py
---------------------------------
Task comment endpoints (nested under a task).
"""

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.task_comment import (
    TaskCommentCreate,
    TaskCommentList,
    TaskCommentResponse,
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
