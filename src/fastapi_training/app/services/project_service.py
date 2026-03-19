from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.project import Project
from ..models.task import Task
from ..schemas.project import ProjectCreate

async def create_project_service(db: AsyncSession, project_data: ProjectCreate, user_id: int) -> Project:
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        user_id=user_id
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

async def get_projects_for_user_service(db: AsyncSession, user_id: int) -> List[Project]:
    result = await db.execute(select(Project).filter(Project.user_id == user_id))
    return list(result.scalars().all())

async def get_project_by_id_service(db: AsyncSession, project_id: int) -> Optional[Project]:
    result = await db.execute(select(Project).filter(Project.id == project_id))
    return result.scalar_first()

async def assign_task_to_project_service(db: AsyncSession, project_id: int, task_id: int, current_user_id: int) -> Dict:
    project = await get_project_by_id_service(db, project_id)
    if not project:
        return {"error": "Project not found", "code": 404}

    if project.user_id != current_user_id:
        return {"error": "Not allowed to assign to this project", "code": 403}

    result = await db.execute(select(Task).filter(Task.id == task_id, Task.is_deleted == False))
    task = result.scalar_first()
    if not task:
        return {"error": "Task not found", "code": 404}

    if task.user_id != current_user_id:
        return {"error": "Not allowed to assign this task", "code": 403}

    task.project_id = project.id
    await db.commit()
    await db.refresh(task)
    return {"success": True, "task": task}
