from ..db.fake_db import fake_tasks_db


def create_task_service(task_data, user_id: int):
    new_task = {
        "id": len(fake_tasks_db) + 1,
        "title": task_data.title,
        "description": task_data.description,
        "status": task_data.status,
        "user_id": user_id,
        "is_deleted": False,
    }

    fake_tasks_db.append(new_task)
    return new_task


def get_tasks_for_user_service(user_id: int):
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id and not task.get("is_deleted", False)
    ]


def get_task_by_id_service(task_id: int):
    for task in fake_tasks_db:
        if task["id"] == task_id and not task.get("is_deleted", False):
            return task
    return None


def update_task_service(task: dict, update_data):
    if update_data.title is not None:
        task["title"] = update_data.title
    if update_data.description is not None:
        task["description"] = update_data.description
    if update_data.status is not None:
        task["status"] = update_data.status
    return task


def delete_task_service(task_id: int):
    for task in fake_tasks_db:
        if task["id"] == task_id:
            task["is_deleted"] = True
            return True
    return False


def filter_tasks_by_status_service(user_id: int, status: str):
    """
    Filter tasks by status for the current user.
    """
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id
        and not task.get("is_deleted", False)
        and task["status"] == status
    ]


def search_tasks_by_title_service(user_id: int, search_query: str):
    """
    Search tasks by title (case-insensitive).
    """
    search_lower = search_query.lower()
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id
        and not task.get("is_deleted", False)
        and search_lower in task["title"].lower()
    ]
