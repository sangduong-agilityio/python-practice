from ..db.fake_db import fake_tasks_db


def create_task_service(task_data, user_id: int):
    new_task = {
        "id": len(fake_tasks_db) + 1,
        "title": task_data.title,
        "description": task_data.description,
        "user_id": user_id,
    }

    fake_tasks_db.append(new_task)
    return new_task


def get_tasks_for_user_service(user_id: int):
    return [
        task for task in fake_tasks_db
        if task["user_id"] == user_id
    ]
