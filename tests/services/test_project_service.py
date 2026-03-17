"""
Tests for project service functions.
"""
import pytest
from src.fastapi_training.app.services.project_service import (
    create_project_service,
    get_projects_for_user_service,
    get_project_by_id_service,
    assign_task_to_project_service,
)
from src.fastapi_training.app.schemas.project import ProjectCreate
from src.fastapi_training.app.schemas.task import TaskCreate
from src.fastapi_training.app.services.task_service import create_task_service
from src.fastapi_training.app.db.fake_db import fake_projects_db, fake_tasks_db


class TestCreateProject:
    """Tests for project creation."""

    def test_create_project_success(self, test_project_data, test_user_db):
        """Test successful project creation."""
        project_in = ProjectCreate(**test_project_data)
        project = create_project_service(project_in, test_user_db["id"])

        assert project["id"] == 1
        assert project["name"] == test_project_data["name"]
        assert project["user_id"] == test_user_db["id"]
        assert project["tasks"] == []

    def test_create_project_increments_id(self, test_project_data, test_user_db):
        """Test that project IDs are incremented."""
        project_in1 = ProjectCreate(name="Project 1")
        project1 = create_project_service(project_in1, test_user_db["id"])

        project_in2 = ProjectCreate(name="Project 2")
        project2 = create_project_service(project_in2, test_user_db["id"])

        assert project1["id"] == 1
        assert project2["id"] == 2

    def test_create_project_with_description(self, test_user_db):
        """Test creating project with description."""
        project_in = ProjectCreate(
            name="My Project",
            description="This is my project"
        )
        project = create_project_service(project_in, test_user_db["id"])

        assert project["description"] == "This is my project"

    def test_create_project_without_description(self, test_user_db):
        """Test creating project without description."""
        project_in = ProjectCreate(name="My Project")
        project = create_project_service(project_in, test_user_db["id"])

        assert project["description"] is None


class TestGetProjectsForUser:
    """Tests for retrieving user projects."""

    def test_get_projects_for_user_empty(self, test_user_db):
        """Test getting projects for user with no projects."""
        projects = get_projects_for_user_service(test_user_db["id"])

        assert projects == []

    def test_get_projects_for_user_single(self, test_project_data, test_user_db):
        """Test getting single project for user."""
        project_in = ProjectCreate(**test_project_data)
        project = create_project_service(project_in, test_user_db["id"])

        projects = get_projects_for_user_service(test_user_db["id"])

        assert len(projects) == 1
        assert projects[0]["id"] == project["id"]

    def test_get_projects_for_user_multiple(self, test_user_db):
        """Test getting multiple projects for user."""
        for i in range(3):
            project_in = ProjectCreate(name=f"Project {i+1}")
            create_project_service(project_in, test_user_db["id"])

        projects = get_projects_for_user_service(test_user_db["id"])

        assert len(projects) == 3

    def test_get_projects_user_isolation(self, test_user_db, test_second_user_db):
        """Test that projects are not mixed between users."""
        # Create projects for user 1
        for i in range(2):
            project_in = ProjectCreate(name=f"User1 Project {i+1}")
            create_project_service(project_in, test_user_db["id"])

        # Create projects for user 2
        for i in range(3):
            project_in = ProjectCreate(name=f"User2 Project {i+1}")
            create_project_service(project_in, test_second_user_db["id"])

        # Get projects for user 1
        projects_user1 = get_projects_for_user_service(test_user_db["id"])
        assert len(projects_user1) == 2

        # Get projects for user 2
        projects_user2 = get_projects_for_user_service(
            test_second_user_db["id"])
        assert len(projects_user2) == 3

    def test_get_projects_populates_tasks(self, test_user_db):
        """Test that returned projects have populated tasks."""
        # Create project
        project_in = ProjectCreate(name="Project with Tasks")
        project = create_project_service(project_in, test_user_db["id"])

        # Create and assign task
        task_in = TaskCreate(title="Task 1")
        task = create_task_service(task_in, test_user_db["id"])
        assign_task_to_project_service(
            project["id"], task["id"], test_user_db["id"])

        # Get projects
        projects = get_projects_for_user_service(test_user_db["id"])

        assert len(projects[0]["tasks"]) == 1
        assert projects[0]["tasks"][0]["id"] == task["id"]


class TestGetProjectById:
    """Tests for retrieving single project."""

    def test_get_project_by_id_success(self, test_project_data, test_user_db):
        """Test retrieving existing project."""
        project_in = ProjectCreate(**test_project_data)
        created_project = create_project_service(
            project_in, test_user_db["id"])

        project = get_project_by_id_service(created_project["id"])

        assert project is not None
        assert project["id"] == created_project["id"]
        assert project["name"] == test_project_data["name"]

    def test_get_project_by_id_nonexistent(self):
        """Test retrieving non-existent project."""
        project = get_project_by_id_service(999)

        assert project is None

    def test_get_project_by_id_with_tasks(self, test_user_db):
        """Test that project with tasks is populated."""
        # Create project
        project_in = ProjectCreate(name="Project with Tasks")
        project = create_project_service(project_in, test_user_db["id"])

        # Create and assign multiple tasks
        for i in range(3):
            task_in = TaskCreate(title=f"Task {i+1}")
            task = create_task_service(task_in, test_user_db["id"])
            assign_task_to_project_service(
                project["id"], task["id"], test_user_db["id"])

        # Get project
        retrieved = get_project_by_id_service(project["id"])

        assert len(retrieved["tasks"]) == 3


class TestAssignTaskToProject:
    """Tests for assigning tasks to projects."""

    def test_assign_task_to_project_success(self, test_user_db):
        """Test successful task assignment."""
        # Create project
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        # Create task
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_user_db["id"])

        # Assign task to project
        result = assign_task_to_project_service(
            project["id"], task["id"], test_user_db["id"]
        )

        assert "success" in result
        assert result["success"] is True
        assert result["task"]["project_id"] == project["id"]

    def test_assign_task_to_project_updates_project_tasks(self, test_user_db):
        """Test that task is added to project's tasks list."""
        # Create project
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        # Create and assign task
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_user_db["id"])

        assign_task_to_project_service(
            project["id"], task["id"], test_user_db["id"]
        )

        # Verify task is in project's tasks list
        assert task["id"] in project["tasks"]

    def test_assign_task_nonexistent_project(self, test_user_db):
        """Test assigning task to non-existent project."""
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_user_db["id"])

        result = assign_task_to_project_service(
            999, task["id"], test_user_db["id"]
        )

        assert "error" in result
        assert result["code"] == 404
        assert "Project not found" in result["error"]

    def test_assign_nonexistent_task_to_project(self, test_user_db):
        """Test assigning non-existent task to project."""
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        result = assign_task_to_project_service(
            project["id"], 999, test_user_db["id"]
        )

        assert "error" in result
        assert result["code"] == 404
        assert "Task not found" in result["error"]

    def test_assign_task_not_owned_by_user(self, test_user_db, test_second_user_db):
        """Test that user cannot assign other user's task."""
        # Create project for user 1
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        # Create task for user 2
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_second_user_db["id"])

        # Try to assign user 2's task to user 1's project
        result = assign_task_to_project_service(
            project["id"], task["id"], test_user_db["id"]
        )

        assert "error" in result
        assert result["code"] == 403
        assert "Not allowed to assign this task" in result["error"]

    def test_assign_task_to_project_not_owned_by_user(self, test_user_db, test_second_user_db):
        """Test that user cannot assign task to other user's project."""
        # Create project for user 1
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        # Create task for user 2
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_second_user_db["id"])

        # Try to assign user 2's task to user 1's project as user 2
        result = assign_task_to_project_service(
            project["id"], task["id"], test_second_user_db["id"]
        )

        assert "error" in result
        assert result["code"] == 403
        assert "Not allowed to assign to this project" in result["error"]

    def test_assign_same_task_multiple_times(self, test_user_db):
        """Test that same task is not added multiple times to project."""
        # Create project
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        # Create task
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_user_db["id"])

        # Assign task twice
        assign_task_to_project_service(
            project["id"], task["id"], test_user_db["id"]
        )
        assign_task_to_project_service(
            project["id"], task["id"], test_user_db["id"]
        )

        # Task should only appear once in project's tasks
        assert project["tasks"].count(task["id"]) == 1

    def test_assign_multiple_tasks_to_project(self, test_user_db):
        """Test assigning multiple tasks to same project."""
        # Create project
        project_in = ProjectCreate(name="Project")
        project = create_project_service(project_in, test_user_db["id"])

        # Create and assign multiple tasks
        for i in range(3):
            task_in = TaskCreate(title=f"Task {i+1}")
            task = create_task_service(task_in, test_user_db["id"])
            assign_task_to_project_service(
                project["id"], task["id"], test_user_db["id"]
            )

        # All tasks should be in project
        assert len(project["tasks"]) == 3
