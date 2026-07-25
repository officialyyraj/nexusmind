"""Tests for project generation."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from app.orchestration.generation_schemas import (
    GenerationConfig,
    Milestone,
    ProjectPlan,
    ProjectStatus,
    ProjectType,
    Task,
    TechStack,
)
from app.orchestration.project_generator import ProjectGenerator


class TestProjectGenerator:
    """Test ProjectGenerator class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = ProjectGenerator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_generator_creation(self):
        """Test generator creation."""
        assert self.generator is not None
        assert self.generator._templates is not None

    def test_analyze_prompt_python(self):
        """Test prompt analysis for Python."""
        analysis = self.generator._analyze_prompt(
            "Create a Python FastAPI web application"
        )
        
        assert analysis["language"] == "python"
        assert analysis["framework"] == "fastapi"
        # Default is WEB_APP unless api/rest is mentioned

    def test_analyze_prompt_typescript(self):
        """Test prompt analysis for TypeScript."""
        analysis = self.generator._analyze_prompt(
            "Build a TypeScript Express API"
        )
        
        assert analysis["language"] == "typescript"
        assert analysis["framework"] == "express"
        assert analysis["project_type"] == ProjectType.API_SERVICE

    def test_analyze_prompt_with_database(self):
        """Test prompt analysis with database."""
        analysis = self.generator._analyze_prompt(
            "Create a FastAPI app with PostgreSQL"
        )
        
        assert analysis["database"] == "postgresql"

    def test_analyze_prompt_microservice(self):
        """Test prompt analysis for microservice."""
        analysis = self.generator._analyze_prompt(
            "Build a microservice in Go"
        )
        
        assert analysis["language"] == "go"
        assert analysis["framework"] == "gin"

    def test_create_tech_stack_python(self):
        """Test tech stack creation for Python."""
        config = GenerationConfig(
            project_name="test-project",
            project_type=ProjectType.WEB_APP,
        )
        analysis = self.generator._analyze_prompt("Create a web app")
        
        stack = self.generator._create_tech_stack(analysis, config)
        
        assert stack.language == "python"
        assert stack.framework == "fastapi"
        assert "pytest" in stack.testing

    def test_create_tech_stack_go(self):
        """Test tech stack creation for Go."""
        config = GenerationConfig(
            project_name="test-project",
            project_type=ProjectType.API_SERVICE,
        )
        analysis = {"language": "go", "framework": "gin"}
        
        stack = self.generator._create_tech_stack(analysis, config)
        
        assert stack.language == "go"
        assert stack.framework == "gin"

    def test_create_folder_structure_python(self):
        """Test folder structure creation for Python."""
        stack = TechStack(language="python", framework="fastapi")
        
        structure = self.generator._create_folder_structure(stack)
        
        assert "app" in structure.directories
        assert "tests" in structure.directories
        assert "requirements.txt" in [f["path"] for f in structure.files]

    def test_create_folder_structure_typescript(self):
        """Test folder structure creation for TypeScript."""
        stack = TechStack(language="typescript", framework="nextjs")
        
        structure = self.generator._create_folder_structure(stack)
        
        assert "src" in structure.directories
        assert "package.json" in [f["path"] for f in structure.files]

    def test_create_milestones(self):
        """Test milestone creation."""
        milestones = self.generator._create_milestones(ProjectType.WEB_APP)
        
        assert len(milestones) == 4
        assert milestones[0].name == "Project Setup"
        assert milestones[1].name == "Core Implementation"

    def test_create_tasks(self):
        """Test task creation."""
        stack = TechStack(language="python", framework="fastapi")
        tasks = self.generator._create_tasks(ProjectType.WEB_APP, stack)
        
        assert len(tasks) > 0
        assert any(t.title == "Initialize project structure" for t in tasks)
        assert any(t.title == "Write unit tests" for t in tasks)

    def test_create_dependencies(self):
        """Test dependency creation."""
        stack = TechStack(
            language="python",
            framework="fastapi",
            database="postgresql",
        )
        
        deps = self.generator._create_dependencies(stack)
        
        assert len(deps) > 0
        assert any(d.package == "fastapi" for d in deps)
        assert any(d.package == "asyncpg" for d in deps)

    def test_get_main_filename(self):
        """Test main filename detection."""
        assert self.generator._get_main_filename("python") == "main.py"
        assert self.generator._get_main_filename("typescript") == "src/index.ts"
        assert self.generator._get_main_filename("go") == "cmd/main.go"
        assert self.generator._get_main_filename("rust") == "src/main.rs"

    def test_get_requirements_filename(self):
        """Test requirements filename detection."""
        assert self.generator._get_requirements_filename("python") == "requirements.txt"
        assert self.generator._get_requirements_filename("typescript") == "package.json"
        assert self.generator._get_requirements_filename("go") == "go.mod"

    def test_generate_main_file_python(self):
        """Test main file generation for Python."""
        plan = ProjectPlan(
            project_name="Test Project",
            project_type=ProjectType.WEB_APP,
            description="A test project",
            tech_stack=TechStack(language="python", framework="fastapi"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="python")
            ),
        )
        
        content = self.generator._generate_main_file(plan)
        
        assert "FastAPI" in content
        assert "Test Project" in content
        assert "uvicorn" in content

    def test_generate_main_file_typescript(self):
        """Test main file generation for TypeScript."""
        plan = ProjectPlan(
            project_name="Test API",
            project_type=ProjectType.API_SERVICE,
            description="An API",
            tech_stack=TechStack(language="typescript", framework="express"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="typescript")
            ),
        )
        
        content = self.generator._generate_main_file(plan)
        
        assert "express" in content
        assert "Welcome to the API" in content

    def test_generate_main_file_go(self):
        """Test main file generation for Go."""
        plan = ProjectPlan(
            project_name="Test Service",
            project_type=ProjectType.MICROSERVICE,
            description="A service",
            tech_stack=TechStack(language="go", framework="gin"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="go")
            ),
        )
        
        content = self.generator._generate_main_file(plan)
        
        assert "package main" in content
        assert "Welcome" in content

    def test_generate_requirements_python(self):
        """Test requirements generation for Python."""
        plan = ProjectPlan(
            project_name="Test",
            project_type=ProjectType.WEB_APP,
            description="",
            tech_stack=TechStack(language="python", framework="fastapi"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="python")
            ),
        )
        
        content = self.generator._generate_requirements(plan)
        
        assert "fastapi" in content
        assert "pytest" in content

    def test_generate_requirements_typescript(self):
        """Test requirements generation for TypeScript."""
        plan = ProjectPlan(
            project_name="Test",
            project_type=ProjectType.API_SERVICE,
            description="",
            tech_stack=TechStack(language="typescript"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="typescript")
            ),
        )
        
        content = self.generator._generate_requirements(plan)
        
        assert "express" in content
        assert "jest" in content

    def test_generate_readme(self):
        """Test README generation."""
        plan = ProjectPlan(
            project_name="My Project",
            project_type=ProjectType.WEB_APP,
            description="A test project",
            tech_stack=TechStack(language="python", framework="fastapi"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="python")
            ),
        )
        
        content = self.generator._generate_readme(plan)
        
        assert "# My Project" in content
        assert "## Tech Stack" in content
        assert "## Getting Started" in content

    def test_generate_gitignore(self):
        """Test .gitignore generation."""
        plan = ProjectPlan(
            project_name="Test",
            project_type=ProjectType.WEB_APP,
            description="",
            tech_stack=TechStack(language="python"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="python")
            ),
        )
        
        content = self.generator._generate_gitignore(plan)
        
        assert ".env" in content
        assert "__pycache__" in content
        assert "node_modules" in content

    def test_generate_dockerfile_python(self):
        """Test Dockerfile generation for Python."""
        plan = ProjectPlan(
            project_name="Test",
            project_type=ProjectType.WEB_APP,
            description="",
            tech_stack=TechStack(language="python", framework="fastapi"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="python")
            ),
        )
        
        content = self.generator._generate_dockerfile(plan)
        
        assert "python" in content
        assert "pip install" in content
        assert "uvicorn" in content

    def test_generate_ci_workflow_python(self):
        """Test CI workflow generation for Python."""
        plan = ProjectPlan(
            project_name="Test",
            project_type=ProjectType.WEB_APP,
            description="",
            tech_stack=TechStack(language="python"),
            folder_structure=self.generator._create_folder_structure(
                TechStack(language="python")
            ),
        )
        
        content = self.generator._generate_ci_workflow(plan)
        
        assert "pytest" in content
        assert "ubuntu-latest" in content

    @pytest.mark.asyncio
    async def test_generate_plan(self):
        """Test full plan generation."""
        config = GenerationConfig(
            project_name="My Project",
            project_type=ProjectType.WEB_APP,
            description="A test web application",
        )
        
        plan = await self.generator.generate_plan(config)
        
        assert plan.project_name == "My Project"
        assert plan.project_type == ProjectType.WEB_APP
        assert len(plan.milestones) > 0
        assert len(plan.tasks) > 0
        assert len(plan.dependencies) > 0

    @pytest.mark.asyncio
    async def test_generate_code(self):
        """Test full code generation."""
        config = GenerationConfig(
            project_name="Test Project",
            project_type=ProjectType.WEB_APP,
            description="A test project",
            output_directory=self.temp_dir,
        )
        
        plan = await self.generator.generate_plan(config)
        files = await self.generator.generate_code(plan, self.temp_dir)
        
        assert len(files) > 0
        
        # Check some files exist
        for file_path in files:
            if "main.py" in file_path or "README.md" in file_path:
                assert Path(file_path).exists()

    @pytest.mark.asyncio
    async def test_generate_full_project(self):
        """Test full project generation."""
        config = GenerationConfig(
            project_name="Full Test Project",
            project_type=ProjectType.WEB_APP,
            description="A complete test project",
            output_directory=self.temp_dir,
            generate_docker=True,
            generate_readme=True,
            generate_tests=True,
            generate_ci=True,
        )
        
        result = await self.generator.generate(config)
        
        assert result.status == ProjectStatus.COMPLETED
        assert len(result.generated_files) > 0
        assert result.progress_percent == 100.0


class TestGenerationSchemas:
    """Test generation schemas."""

    def test_project_type_values(self):
        """Test ProjectType enum."""
        assert ProjectType.WEB_APP.value == "web_app"
        assert ProjectType.API_SERVICE.value == "api_service"
        assert ProjectType.MICROSERVICE.value == "microservice"

    def test_project_status_values(self):
        """Test ProjectStatus enum."""
        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.GENERATING.value == "generating"
        assert ProjectStatus.COMPLETED.value == "completed"

    def test_tech_stack(self):
        """Test TechStack schema."""
        stack = TechStack(
            language="python",
            framework="fastapi",
            database="postgresql",
        )
        
        assert stack.language == "python"
        assert stack.framework == "fastapi"
        assert stack.database == "postgresql"

    def test_milestone(self):
        """Test Milestone schema."""
        milestone = Milestone(
            id="m1",
            name="Test Milestone",
            description="A test milestone",
            tasks=["t1", "t2"],
        )
        
        assert milestone.id == "m1"
        assert len(milestone.tasks) == 2

    def test_task(self):
        """Test Task schema."""
        task = Task(
            id="t1",
            title="Test Task",
            description="A test task",
            priority=1,
            estimated_hours=2.0,
        )
        
        assert task.id == "t1"
        assert task.priority == 1
        assert task.estimated_hours == 2.0

    def test_generation_config(self):
        """Test GenerationConfig schema."""
        config = GenerationConfig(
            project_name="Test",
            project_type=ProjectType.WEB_APP,
            generate_docker=True,
            generate_ci=True,
        )
        
        assert config.project_name == "Test"
        assert config.generate_docker is True


class TestIntegration:
    """Integration tests."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = ProjectGenerator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_end_to_end_python_fastapi(self):
        """Test end-to-end Python FastAPI project generation."""
        config = GenerationConfig(
            project_name="My FastAPI App",
            project_type=ProjectType.WEB_APP,
            description="A FastAPI application with PostgreSQL",
            output_directory=self.temp_dir,
        )
        
        result = await self.generator.generate(config)
        
        assert result.status == ProjectStatus.COMPLETED
        assert result.plan is not None
        assert len(result.generated_files) > 0
        
        # Check key files exist
        project_dir = Path(self.temp_dir) / "my_fastapi_app"
        assert (project_dir / "main.py").exists()
        assert (project_dir / "requirements.txt").exists()
        assert (project_dir / "Dockerfile").exists()
        assert (project_dir / "README.md").exists()

    @pytest.mark.asyncio
    async def test_end_to_end_typescript_express(self):
        """Test end-to-end TypeScript Express project generation."""
        config = GenerationConfig(
            project_name="My Express API",
            project_type=ProjectType.API_SERVICE,
            description="A TypeScript Express API",
            output_directory=self.temp_dir,
        )
        
        result = await self.generator.generate(config)
        
        assert result.status == ProjectStatus.COMPLETED
        
        project_dir = Path(self.temp_dir) / "my_express_api"
        assert (project_dir / "src" / "index.ts").exists()
        assert (project_dir / "package.json").exists()

    @pytest.mark.asyncio
    async def test_end_to_end_go_gin(self):
        """Test end-to-end Go Gin project generation."""
        config = GenerationConfig(
            project_name="My Gin Service",
            project_type=ProjectType.MICROSERVICE,
            description="A Go Gin microservice",
            output_directory=self.temp_dir,
        )
        
        result = await self.generator.generate(config)
        
        assert result.status == ProjectStatus.COMPLETED
        
        project_dir = Path(self.temp_dir) / "my_gin_service"
        assert (project_dir / "cmd" / "main.go").exists()
        assert (project_dir / "go.mod").exists()
