from typing import List, Optional, Dict
from ..db.fake_db import fake_projects_db, fake_tasks_db


def create_project_service(project_data, user_id: int) -> dict:
    """
    Create a new project for the current user.

    Args:
        project_data: ProjectCreate schema with name and optional description
        user_id: ID of the project owner

    Returns:
        Dictionary containing newly created project (id, name, description, user_id)
    """
    new_project = {
        "id": len(fake_projects_db) + 1,
        "name": project_data.name,
        "description": project_data.description,
        "user_id": user_id,
    }
    fake_projects_db.append(new_project)
    return new_project


def get_projects_for_user_service(user_id: int) -> List[dict]:
    """
    Get all projects for the current user.

    Args:
        user_id: ID of the user

    Returns:
        List of project dictionaries belonging to the user
    """
    return [
        project for project in fake_projects_db
        if project["user_id"] == user_id
    ]


def get_project_by_id_service(project_id: int) -> Optional[dict]:
    """
    Get a project by ID.

    Args:
        project_id: ID of the project to retrieve

    Returns:
        Project dictionary if found, None otherwise
    """
    for project in fake_projects_db:
        if project["id"] == project_id:
            return project
    return None


def assign_task_to_project_service(project_id: int, task_id: int, current_user_id: int) -> Dict:
    """
    Assign a task to a project with full authorization checks.

    Acceptance Criteria:
    - Only assign own task (task must belong to current user)
    - Proper validation (task & project must exist)
    - Authorization enforced (project must belong to current user)

    Args:
        project_id: ID of the project
        task_id: ID of the task to assign
        current_user_id: ID of the current authenticated user

    Returns:
        Dictionary with success status and task data, or error info with HTTP code
    """
    # Check project exists and belongs to current user
    project = get_project_by_id_service(project_id)
    if not project:
        return {"error": "Project not found", "code": 404}

    if project["user_id"] != current_user_id:
        return {"error": "Not allowed to assign to this project", "code": 403}

    # Check task exists and belongs to current user
    task = None
    for t in fake_tasks_db:
        if t["id"] == task_id:
            task = t
            break

    if not task:
        return {"error": "Task not found", "code": 404}

    if task["user_id"] != current_user_id:
        return {"error": "Not allowed to assign this task", "code": 403}

    # Assign task to project
    task["project_id"] = project_id
    return {"success": True, "task": task}
