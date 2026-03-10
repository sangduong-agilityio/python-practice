from typing import List, Dict, Optional
from ..db.fake_db import fake_tasks_db


def create_task_service(task_data, user_id: int) -> dict:
    """
    Create a new task for the given user.

    Args:
        task_data: TaskCreate schema with title, description, status, project_id
        user_id: ID of the task owner

    Returns:
        Dictionary containing created task with id, title, user_id, etc.
    """
    new_task = {
        "id": len(fake_tasks_db) + 1,
        "title": task_data.title,
        "description": task_data.description,
        "status": task_data.status,
        "user_id": user_id,
        "project_id": task_data.project_id,
        "is_deleted": False,
    }

    fake_tasks_db.append(new_task)
    return new_task


def get_tasks_for_user_service(user_id: int) -> List[dict]:
    """
    Get all non-deleted tasks for the given user.

    Args:
        user_id: ID of the user

    Returns:
        List of task dictionaries belonging to the user
    """
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id and not task.get("is_deleted", False)
    ]


def get_task_by_id_service(task_id: int) -> Optional[dict]:
    """
    Get a specific task by ID (returns None if not found or deleted).

    Args:
        task_id: ID of the task to retrieve

    Returns:
        Task dictionary if found and not deleted, None otherwise
    """
    for task in fake_tasks_db:
        if task["id"] == task_id and not task.get("is_deleted", False):
            return task
    return None


def update_task_service(task: dict, update_data) -> dict:
    """
    Update task fields with provided data (partial update).

    Args:
        task: Existing task dictionary to update
        update_data: TaskUpdate schema with optional fields to update

    Returns:
        Updated task dictionary
    """
    if update_data.title is not None:
        task["title"] = update_data.title
    if update_data.description is not None:
        task["description"] = update_data.description
    if update_data.status is not None:
        task["status"] = update_data.status
    if update_data.project_id is not None:
        task["project_id"] = update_data.project_id
    return task


def delete_task_service(task_id: int) -> bool:
    """
    Soft delete a task by marking it as deleted.

    Args:
        task_id: ID of the task to delete

    Returns:
        True if task was deleted, False if task not found
    """
    for task in fake_tasks_db:
        if task["id"] == task_id:
            task["is_deleted"] = True
            return True
    return False


def filter_tasks_by_status_service(user_id: int, status: str) -> List[dict]:
    """
    Filter tasks by status for the current user.

    Args:
        user_id: ID of the user
        status: Task status to filter by (pending, in_progress, completed)

    Returns:
        List of task dictionaries matching the status filter
    """
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id
        and not task.get("is_deleted", False)
        and task["status"] == status
    ]


def search_tasks_by_title_service(user_id: int, search_query: str) -> List[dict]:
    """
    Search tasks by title (case-insensitive partial match).

    Args:
        user_id: ID of the user
        search_query: Search string to match against task titles

    Returns:
        List of task dictionaries matching the search query
    """
    search_lower = search_query.lower()
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id
        and not task.get("is_deleted", False)
        and search_lower in task["title"].lower()
    ]
