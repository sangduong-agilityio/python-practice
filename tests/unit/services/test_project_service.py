"""Tests for project service."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_training.services import project_service
from src.fastapi_training.models.project import Project
from src.fastapi_training.models.task import Task
from src.fastapi_training.schemas.project import ProjectCreate


@pytest.fixture
def mock_db() -> AsyncSession:
    """Mock database session."""
    return None


@pytest.mark.asyncio
class TestProjectService:
    """Test cases for project service business logic."""

    @patch("src.fastapi_training.services.project_service.project_crud.create_project_db", new_callable=AsyncMock)
    async def test_create_project_success(self, mock_create_db, mock_db):
        """Test creating a new project successfully."""
        # Setup
        mock_project = Project(
            id=1,
            name="Test Project",
            description="Test description",
            user_id=1,
            is_deleted=False,
        )
        mock_create_db.return_value = mock_project

        # Execute
        project_in = ProjectCreate(
            name="Test Project",
            description="Test description",
        )
        result = await project_service.create_project(mock_db, project_in, user_id=1)

        # Assert
        assert result.name == "Test Project"
        assert result.user_id == 1
        mock_create_db.assert_called_once()

    @patch("src.fastapi_training.services.project_service.project_crud.get_projects_for_user", new_callable=AsyncMock)
    async def test_get_projects_for_user(self, mock_get_projects, mock_db):
        """Test retrieving all projects for a user."""
        # Setup
        mock_projects = [
            Project(id=1, name="Project 1", description="Desc 1",
                    user_id=1, is_deleted=False),
            Project(id=2, name="Project 2", description="Desc 2",
                    user_id=1, is_deleted=False),
        ]
        mock_get_projects.return_value = mock_projects

        # Execute
        result = await project_service.get_projects_for_user(mock_db, user_id=1)

        # Assert
        assert len(result) == 2
        assert result[0].name == "Project 1"
        mock_get_projects.assert_called_once_with(mock_db, 1)

    @patch("src.fastapi_training.services.project_service.project_crud.get_project_by_id", new_callable=AsyncMock)
    async def test_get_project_by_id(self, mock_get_project, mock_db):
        """Test retrieving a single project by ID."""
        # Setup
        mock_project = Project(
            id=1, name="Test Project", description="Desc", user_id=1, is_deleted=False
        )
        mock_get_project.return_value = mock_project

        # Execute
        result = await project_service.get_project_by_id(mock_db, project_id=1)

        # Assert
        assert result.id == 1
        assert result.name == "Test Project"
        mock_get_project.assert_called_once_with(mock_db, 1)

    @patch("src.fastapi_training.services.project_service.project_crud.get_project_by_id", new_callable=AsyncMock)
    async def test_assign_task_to_project_project_not_found(self, mock_get_project, mock_db):
        """Test assign task fails if project not found."""
        # Setup
        mock_get_project.return_value = None

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await project_service.assign_task_to_project(
                mock_db, project_id=999, task_id=1, current_user_id=1
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Project not found"

    @patch("src.fastapi_training.services.project_service.project_crud.get_project_by_id", new_callable=AsyncMock)
    async def test_assign_task_to_project_forbidden(self, mock_get_project, mock_db):
        """Test assign task fails if user doesn't own project."""
        # Setup
        mock_project = Project(
            id=1, name="Project 1", description="Desc", user_id=2, is_deleted=False  # Different owner
        )
        mock_get_project.return_value = mock_project

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await project_service.assign_task_to_project(
                mock_db, project_id=1, task_id=1, current_user_id=1
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Not allowed to assign to this project"

    @patch("src.fastapi_training.services.project_service.project_crud.get_project_by_id", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.project_service.project_crud.get_task_for_project", new_callable=AsyncMock)
    async def test_assign_task_to_project_task_not_found(self, mock_get_task, mock_get_project, mock_db):
        """Test assign task fails if task not found."""
        # Setup
        mock_project = Project(
            id=1, name="Project 1", description="Desc", user_id=1, is_deleted=False
        )
        mock_get_project.return_value = mock_project
        mock_get_task.return_value = None

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await project_service.assign_task_to_project(
                mock_db, project_id=1, task_id=999, current_user_id=1
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Task not found"

    @patch("src.fastapi_training.services.project_service.project_crud.get_project_by_id", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.project_service.project_crud.get_task_for_project", new_callable=AsyncMock)
    async def test_assign_task_to_project_task_forbidden(self, mock_get_task, mock_get_project, mock_db):
        """Test assign task fails if user doesn't own task."""
        # Setup
        mock_project = Project(
            id=1, name="Project 1", description="Desc", user_id=1, is_deleted=False
        )
        mock_task = Task(
            id=1,
            title="Task 1",
            description="Desc",
            status="pending",
            user_id=2,  # Different owner
            is_deleted=False,
        )
        mock_get_project.return_value = mock_project
        mock_get_task.return_value = mock_task

        # Execute & Assert
        with pytest.raises(HTTPException) as exc_info:
            await project_service.assign_task_to_project(
                mock_db, project_id=1, task_id=1, current_user_id=1
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Not allowed to assign this task"

    @patch("src.fastapi_training.services.project_service.project_crud.get_project_by_id", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.project_service.project_crud.get_task_for_project", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.project_service.project_crud.assign_task_to_project_db", new_callable=AsyncMock)
    async def test_assign_task_to_project_success(self, mock_assign, mock_get_task, mock_get_project, mock_db):
        """Test successfully assigning task to project."""
        # Setup
        mock_project = Project(
            id=1, name="Project 1", description="Desc", user_id=1, is_deleted=False
        )
        mock_task = Task(
            id=1,
            title="Task 1",
            description="Desc",
            status="pending",
            user_id=1,
            project_id=None,
            is_deleted=False,
        )
        assigned_task = Task(
            id=1,
            title="Task 1",
            description="Desc",
            status="pending",
            user_id=1,
            project_id=1,  # Now assigned to project
            is_deleted=False,
        )
        mock_get_project.return_value = mock_project
        mock_get_task.return_value = mock_task
        mock_assign.return_value = assigned_task

        # Execute
        result = await project_service.assign_task_to_project(
            mock_db, project_id=1, task_id=1, current_user_id=1
        )

        # Assert
        assert result.project_id == 1
        mock_assign.assert_called_once()
