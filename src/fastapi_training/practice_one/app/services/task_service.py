from ..db.fake_db import fake_tasks_db


def create_task_service(task_data, user_id: int):
    new_task = {
        "id": len(fake_tasks_db) + 1,
        "title": task_data.title,
        "description": task_data.description,
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
    return task


def delete_task_service(task_id: int):
    for task in fake_tasks_db:
        if task["id"] == task_id:
            task["is_deleted"] = True
            return True
    return False
