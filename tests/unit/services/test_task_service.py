"""Tests for task service."""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_training.services import task_service
from src.fastapi_training.models.task import Task
from src.fastapi_training.schemas.task import TaskCreate, TaskUpdate


@pytest.fixture
def mock_db() -> AsyncSession:
    """Mock database session."""
    return None


@pytest.mark.asyncio
class TestTaskService:
    """Test cases for task service business logic."""

    @patch("src.fastapi_training.services.task_service.task_crud.create_task_db", new_callable=AsyncMock)
    async def test_create_task_success(self, mock_create_db, mock_db):
        """Test creating a new task successfully."""
        # Setup
        mock_task = Task(
            id=1,
            title="Test Task",
            description="Test description",
            status="pending",
            user_id=1,
            project_id=None,
            is_deleted=False,
        )
        mock_create_db.return_value = mock_task

        # Execute
        task_in = TaskCreate(
            title="Test Task",
            description="Test description",
            status="pending",
            project_id=None,
        )
        result = await task_service.create_task(mock_db, task_in, user_id=1)

        # Assert
        assert result.title == "Test Task"
        assert result.user_id == 1
        mock_create_db.assert_called_once()

    @patch("src.fastapi_training.services.task_service.task_crud.get_tasks_for_user", new_callable=AsyncMock)
    async def test_get_tasks_for_user(self, mock_get_tasks, mock_db):
        """Test retrieving all tasks for a user."""
        # Setup
        mock_tasks = [
            Task(id=1, title="Task 1", description="Desc 1",
                 status="pending", user_id=1, is_deleted=False),
            Task(id=2, title="Task 2", description="Desc 2",
                 status="done", user_id=1, is_deleted=False),
        ]
        mock_get_tasks.return_value = mock_tasks

        # Execute
        result = await task_service.get_tasks_for_user(mock_db, user_id=1)

        # Assert
        assert len(result) == 2
        assert result[0].title == "Task 1"
        mock_get_tasks.assert_called_once_with(mock_db, 1)

    @patch("src.fastapi_training.services.task_service.task_crud.get_task_by_id", new_callable=AsyncMock)
    async def test_get_task_by_id(self, mock_get_task, mock_db):
        """Test retrieving a single task by ID."""
        # Setup
        mock_task = Task(
            id=1, title="Test Task", description="Desc", status="pending", user_id=1, is_deleted=False
        )
        mock_get_task.return_value = mock_task

        # Execute
        result = await task_service.get_task_by_id(mock_db, task_id=1)

        # Assert
        assert result.id == 1
        assert result.title == "Test Task"
        mock_get_task.assert_called_once_with(mock_db, 1)

    @patch("src.fastapi_training.services.task_service.task_crud.update_task_db", new_callable=AsyncMock)
    async def test_update_task(self, mock_update_db, mock_db):
        """Test updating a task."""
        # Setup
        old_task = Task(
            id=1, title="Old Title", description="Old Desc", status="pending", user_id=1, is_deleted=False
        )
        updated_task = Task(
            id=1, title="New Title", description="Old Desc", status="pending", user_id=1, is_deleted=False
        )
        mock_update_db.return_value = updated_task

        # Execute
        update_data = TaskUpdate(title="New Title")
        result = await task_service.update_task(mock_db, old_task, update_data)

        # Assert
        assert result.title == "New Title"
        mock_update_db.assert_called_once()

    @patch("src.fastapi_training.services.task_service.task_crud.get_task_by_id", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.task_service.task_crud.soft_delete_task", new_callable=AsyncMock)
    async def test_delete_task_success(self, mock_soft_delete, mock_get_task, mock_db):
        """Test soft deleting a task."""
        # Setup
        mock_task = Task(
            id=1, title="Test Task", description="Desc", status="pending", user_id=1, is_deleted=False
        )
        mock_get_task.return_value = mock_task
        mock_soft_delete.return_value = True

        # Execute
        result = await task_service.delete_task(mock_db, task_id=1)

        # Assert
        assert result is True
        mock_soft_delete.assert_called_once()

    @patch("src.fastapi_training.services.task_service.task_crud.get_task_by_id", new_callable=AsyncMock)
    async def test_delete_task_not_found(self, mock_get_task, mock_db):
        """Test delete returns False if task not found."""
        # Setup
        mock_get_task.return_value = None

        # Execute
        result = await task_service.delete_task(mock_db, task_id=999)

        # Assert
        assert result is False

    @patch("src.fastapi_training.services.task_service.task_crud.filter_tasks_by_status", new_callable=AsyncMock)
    async def test_filter_tasks_by_status(self, mock_filter, mock_db):
        """Test filtering tasks by status."""
        # Setup
        mock_tasks = [
            Task(id=1, title="Task 1", description="Desc",
                 status="done", user_id=1, is_deleted=False),
        ]
        mock_filter.return_value = mock_tasks

        # Execute
        result = await task_service.filter_tasks_by_status(mock_db, user_id=1, task_status="done")

        # Assert
        assert len(result) == 1
        assert result[0].status == "done"
        mock_filter.assert_called_once()

    @patch("src.fastapi_training.services.task_service.task_crud.search_tasks_by_title", new_callable=AsyncMock)
    async def test_search_tasks_by_title(self, mock_search, mock_db):
        """Test searching tasks by title."""
        # Setup
        mock_tasks = [
            Task(id=1, title="Important Task", description="Desc",
                 status="pending", user_id=1, is_deleted=False),
        ]
        mock_search.return_value = mock_tasks

        # Execute
        result = await task_service.search_tasks_by_title(mock_db, user_id=1, search_query="Important")

        # Assert
        assert len(result) == 1
        assert "Important" in result[0].title
        mock_search.assert_called_once()
