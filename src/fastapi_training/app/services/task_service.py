from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate

async def create_task_service(db: AsyncSession, task_data: TaskCreate, user_id: int) -> Task:
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        user_id=user_id,
        project_id=task_data.project_id,
        is_deleted=False
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

async def get_tasks_for_user_service(db: AsyncSession, user_id: int) -> List[Task]:
    result = await db.execute(select(Task).filter(Task.user_id == user_id, Task.is_deleted == False))
    return list(result.scalars().all())

async def get_task_by_id_service(db: AsyncSession, task_id: int) -> Optional[Task]:
    result = await db.execute(select(Task).filter(Task.id == task_id, Task.is_deleted == False))
    return result.scalar_first()

async def update_task_service(db: AsyncSession, task: Task, update_data: TaskUpdate) -> Task:
    update_dict = update_data.model_dump(exclude_unset=True) if hasattr(update_data, 'model_dump') else update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task_service(db: AsyncSession, task_id: int) -> bool:
    task = await get_task_by_id_service(db, task_id)
    if not task:
        return False
    task.is_deleted = True
    await db.commit()
    return True

async def filter_tasks_by_status_service(db: AsyncSession, user_id: int, status: str) -> List[Task]:
    result = await db.execute(
        select(Task).filter(Task.user_id == user_id, Task.is_deleted == False, Task.status == status)
    )
    return list(result.scalars().all())

async def search_tasks_by_title_service(db: AsyncSession, user_id: int, search_query: str) -> List[Task]:
    result = await db.execute(
        select(Task).filter(Task.user_id == user_id, Task.is_deleted == False, Task.title.ilike(f"%{search_query}%"))
    )
    return list(result.scalars().all())
