"""Autonomous project generator."""

import asyncio
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.agents.types import AgentType
from app.orchestration.generation_schemas import (
    CodeTemplate,
    Dependency,
    FolderStructure,
    GenerationConfig,
    GeneratedFile,
    Milestone,
    ProjectGeneration,
    ProjectPlan,
    ProjectStatus,
    ProjectType,
    Task,
    TechStack,
)


class ProjectGenerator:
    """Autonomous project generator from natural language."""

    def __init__(self):
        """Initialize generator."""
        self._templates = self._load_templates()
        self._generation: ProjectGeneration | None = None

    def _load_templates(self) -> dict[str, Any]:
        """Load code templates."""
        return {
            "python_fastapi": self._fastapi_template(),
            "python_flask": self._flask_template(),
            "nextjs": self._nextjs_template(),
            "nodejs_express": self._express_template(),
            "go_gin": self._gin_template(),
            "rust_actix": self._actix_template(),
            "docker": self._docker_template(),
            "docker_compose": self._docker_compose_template(),
            "github_actions": self._github_actions_template(),
            "pytest": self._pytest_template(),
        }

    # ===== Template Methods =====

    def _fastapi_template(self) -> dict[str, Any]:
        """FastAPI project template."""
        return {
            "structure": [
                "app/",
                "app/api/",
                "app/core/",
                "app/models/",
                "app/schemas/",
                "app/services/",
                "tests/",
            ],
            "files": {
                "main.py": "fastapi_main",
                "requirements.txt": "fastapi_requirements",
                "app/__init__.py": "",
                "app/api/__init__.py": "",
                "app/core/__init__.py": "",
                "app/models/__init__.py": "",
                "app/schemas/__init__.py": "",
                "app/services/__init__.py": "",
                "tests/__init__.py": "",
            },
        }

    def _flask_template(self) -> dict[str, Any]:
        """Flask project template."""
        return {
            "structure": [
                "app/",
                "app/routes/",
                "app/models/",
                "tests/",
            ],
            "files": {
                "app.py": "flask_main",
                "requirements.txt": "flask_requirements",
                "config.py": "flask_config",
            },
        }

    def _nextjs_template(self) -> dict[str, Any]:
        """Next.js project template."""
        return {
            "structure": [
                "app/",
                "app/components/",
                "app/pages/",
                "app/styles/",
                "public/",
                "tests/",
            ],
            "files": {
                "package.json": "nextjs_package",
                "next.config.js": "",
                "tsconfig.json": "",
            },
        }

    def _express_template(self) -> dict[str, Any]:
        """Express.js project template."""
        return {
            "structure": [
                "src/",
                "src/routes/",
                "src/controllers/",
                "src/models/",
                "tests/",
            ],
            "files": {
                "package.json": "express_package",
                "src/app.js": "express_app",
            },
        }

    def _gin_template(self) -> dict[str, Any]:
        """Gin project template."""
        return {
            "structure": [
                "cmd/",
                "internal/",
                "internal/handlers/",
                "internal/models/",
                "pkg/",
                "tests/",
            ],
            "files": {
                "go.mod": "go_mod",
                "cmd/main.go": "go_main",
            },
        }

    def _actix_template(self) -> dict[str, Any]:
        """Actix-web project template."""
        return {
            "structure": [
                "src/",
                "src/handlers/",
                "src/models/",
                "tests/",
            ],
            "files": {
                "Cargo.toml": "rust_cargo",
                "src/main.rs": "rust_main",
            },
        }

    def _docker_template(self) -> dict[str, Any]:
        """Docker template."""
        return {
            "structure": [],
            "files": {
                "Dockerfile": "dockerfile",
            },
        }

    def _docker_compose_template(self) -> dict[str, Any]:
        """Docker Compose template."""
        return {
            "structure": [],
            "files": {
                "docker-compose.yml": "docker_compose",
            },
        }

    def _github_actions_template(self) -> dict[str, Any]:
        """GitHub Actions template."""
        return {
            "structure": [".github/workflows/"],
            "files": {
                ".github/workflows/ci.yml": "ci_workflow",
            },
        }

    def _pytest_template(self) -> dict[str, Any]:
        """Pytest template."""
        return {
            "structure": ["tests/"],
            "files": {
                "pytest.ini": "",
                "conftest.py": "",
            },
        }

    # ===== Analysis Methods =====

    def _analyze_prompt(self, prompt: str) -> dict[str, Any]:
        """Analyze natural language prompt to extract requirements."""
        prompt_lower = prompt.lower()

        # Detect project type
        project_type = ProjectType.WEB_APP
        if any(word in prompt_lower for word in ["api", "rest", "backend", "microservice"]):
            project_type = ProjectType.API_SERVICE
        elif any(word in prompt_lower for word in ["cli", "command-line", "terminal"]):
            project_type = ProjectType.CLI_TOOL
        elif any(word in prompt_lower for word in ["library", "package", "sdk"]):
            project_type = ProjectType.LIBRARY
        elif any(word in prompt_lower for word in ["frontend", "react", "vue", "angular", "next"]):
            project_type = ProjectType.FULLSTACK_APP
        elif any(word in prompt_lower for word in ["pipeline", "etl", "data"]):
            project_type = ProjectType.DATA_PIPELINE

        # Detect language
        language = "python"
        if "typescript" in prompt_lower or "ts" in prompt_lower:
            language = "typescript"
        elif "go" in prompt_lower or "golang" in prompt_lower:
            language = "go"
        elif "rust" in prompt_lower:
            language = "rust"
        elif "java" in prompt_lower:
            language = "java"
        elif "node" in prompt_lower or "javascript" in prompt_lower:
            language = "javascript"

        # Detect framework
        framework = None
        if language == "python":
            if "fastapi" in prompt_lower:
                framework = "fastapi"
            elif "flask" in prompt_lower:
                framework = "flask"
            elif "django" in prompt_lower:
                framework = "django"
        elif language == "typescript":
            if "next" in prompt_lower:
                framework = "nextjs"
            elif "express" in prompt_lower:
                framework = "express"
            elif "nest" in prompt_lower:
                framework = "nestjs"
        elif language == "go":
            framework = "gin"
        elif language == "rust":
            framework = "actix"

        # Detect database
        database = None
        if any(word in prompt_lower for word in ["postgres", "postgresql"]):
            database = "postgresql"
        elif "mysql" in prompt_lower:
            database = "mysql"
        elif "mongo" in prompt_lower:
            database = "mongodb"
        elif "sqlite" in prompt_lower:
            database = "sqlite"
        elif "redis" in prompt_lower:
            database = "redis"

        # Detect cloud
        cloud = None
        if "aws" in prompt_lower or "amazon" in prompt_lower:
            cloud = "aws"
        elif "gcp" in prompt_lower or "google" in prompt_lower:
            cloud = "gcp"
        elif "azure" in prompt_lower:
            cloud = "azure"
        elif "kubernetes" in prompt_lower or "k8s" in prompt_lower:
            cloud = "kubernetes"

        return {
            "project_type": project_type,
            "language": language,
            "framework": framework,
            "database": database,
            "cloud": cloud,
        }

    def _create_tech_stack(self, analysis: dict[str, Any], config: GenerationConfig) -> TechStack:
        """Create tech stack from analysis."""
        language = config.tech_stack.language if config.tech_stack else analysis.get("language", "python")
        framework = config.tech_stack.framework if config.tech_stack else analysis.get("framework")

        # Set default framework based on language
        if not framework:
            if language == "python":
                framework = "fastapi"
            elif language == "typescript":
                framework = "nextjs"
            elif language == "go":
                framework = "gin"
            elif language == "rust":
                framework = "actix"

        return TechStack(
            language=language,
            framework=framework,
            backend=framework if analysis.get("project_type") in [ProjectType.API_SERVICE, ProjectType.MICROSERVICE] else None,
            frontend="react" if analysis.get("project_type") == ProjectType.FULLSTACK_APP else None,
            database=analysis.get("database"),
            testing=["pytest", "pytest-cov"] if language == "python" else ["jest"],
            ci_cd=["github-actions"],
            cloud=analysis.get("cloud"),
        )

    def _create_folder_structure(self, tech_stack: TechStack) -> FolderStructure:
        """Create folder structure based on tech stack."""
        directories = []
        files = []
        hidden = [".gitignore", ".env.example"]

        if tech_stack.language == "python":
            directories = ["app", "app/api", "app/core", "app/models", "app/schemas", "tests"]
            files = [
                {"path": "requirements.txt", "description": "Python dependencies"},
                {"path": "setup.py", "description": "Package setup"},
                {"path": "pytest.ini", "description": "Pytest config"},
                {"path": ".env.example", "description": "Environment variables"},
            ]
        elif tech_stack.language == "typescript":
            directories = ["src", "src/components", "src/pages", "tests"]
            files = [
                {"path": "package.json", "description": "Node dependencies"},
                {"path": "tsconfig.json", "description": "TypeScript config"},
                {"path": ".env.example", "description": "Environment variables"},
            ]
        elif tech_stack.language == "go":
            directories = ["cmd", "internal", "internal/handlers", "internal/models", "pkg", "tests"]
            files = [
                {"path": "go.mod", "description": "Go module"},
                {"path": "Makefile", "description": "Build commands"},
            ]
        elif tech_stack.language == "rust":
            directories = ["src", "src/handlers", "src/models", "tests"]
            files = [
                {"path": "Cargo.toml", "description": "Rust dependencies"},
            ]

        return FolderStructure(
            root="project",
            directories=directories,
            files=files,
            hidden_files=hidden,
        )

    def _create_milestones(self, project_type: ProjectType) -> list[Milestone]:
        """Create project milestones."""
        milestones = [
            Milestone(
                id="m1",
                name="Project Setup",
                description="Initialize project, configure tools",
                tasks=["t1", "t2"],
                estimated_hours=2.0,
            ),
            Milestone(
                id="m2",
                name="Core Implementation",
                description="Implement main features",
                tasks=["t3", "t4", "t5"],
                estimated_hours=8.0,
            ),
            Milestone(
                id="m3",
                name="Testing & Documentation",
                description="Write tests and documentation",
                tasks=["t6", "t7"],
                estimated_hours=4.0,
            ),
            Milestone(
                id="m4",
                name="Deployment",
                description="Docker and CI/CD setup",
                tasks=["t8", "t9"],
                estimated_hours=2.0,
            ),
        ]
        return milestones

    def _create_tasks(self, project_type: ProjectType, tech_stack: TechStack) -> list[Task]:
        """Create project tasks."""
        tasks = [
            Task(
                id="t1",
                title="Initialize project structure",
                description="Create folder structure and basic files",
                priority=1,
                estimated_hours=1.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=["setup.py", "requirements.txt"],
            ),
            Task(
                id="t2",
                title="Configure development environment",
                description="Setup linting, formatting, pre-commit hooks",
                priority=2,
                estimated_hours=1.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=[".pre-commit-config.yaml"],
                dependencies=["t1"],
            ),
            Task(
                id="t3",
                title="Implement core models",
                description="Create data models and schemas",
                priority=1,
                estimated_hours=2.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=["app/models/"],
                dependencies=["t1"],
            ),
            Task(
                id="t4",
                title="Implement API endpoints",
                description="Create REST API endpoints",
                priority=1,
                estimated_hours=3.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=["app/api/"],
                dependencies=["t3"],
            ),
            Task(
                id="t5",
                title="Implement business logic",
                description="Create service layer",
                priority=2,
                estimated_hours=3.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=["app/services/"],
                dependencies=["t3"],
            ),
            Task(
                id="t6",
                title="Write unit tests",
                description="Create test suite",
                priority=2,
                estimated_hours=2.0,
                assigned_agent=AgentType.TESTER.value,
                files_to_create=["tests/"],
                dependencies=["t4"],
            ),
            Task(
                id="t7",
                title="Write documentation",
                description="Create README and API docs",
                priority=3,
                estimated_hours=2.0,
                assigned_agent=AgentType.DOCUMENTATION.value,
                files_to_create=["README.md", "docs/"],
                dependencies=["t4"],
            ),
            Task(
                id="t8",
                title="Create Docker configuration",
                description="Setup Dockerfile and docker-compose",
                priority=2,
                estimated_hours=1.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=["Dockerfile", "docker-compose.yml"],
                dependencies=["t4"],
            ),
            Task(
                id="t9",
                title="Setup CI/CD pipeline",
                description="Create GitHub Actions workflow",
                priority=3,
                estimated_hours=1.0,
                assigned_agent=AgentType.CODER.value,
                files_to_create=[".github/workflows/ci.yml"],
                dependencies=["t8"],
            ),
        ]
        return tasks

    def _create_dependencies(self, tech_stack: TechStack) -> list[Dependency]:
        """Create project dependencies."""
        deps = []

        if tech_stack.language == "python":
            deps = [
                Dependency(package="fastapi", version="^0.100.0"),
                Dependency(package="uvicorn", version="^0.23.0"),
                Dependency(package="pydantic", version="^2.0.0"),
                Dependency(package="pytest", version="^7.0.0"),
                Dependency(package="pytest-asyncio", version="^0.21.0"),
            ]
            if tech_stack.database:
                if "postgres" in tech_stack.database:
                    deps.append(Dependency(package="asyncpg", version="^0.28.0"))
                elif "mysql" in tech_stack.database:
                    deps.append(Dependency(package="aiomysql", version="^0.2.0"))
                elif "mongo" in tech_stack.database:
                    deps.append(Dependency(package="motor", version="^3.3.0"))

        return deps

    # ===== Generation Methods =====

    async def generate_plan(self, config: GenerationConfig) -> ProjectPlan:
        """Generate project plan from configuration."""
        analysis = self._analyze_prompt(config.description or config.project_name)

        tech_stack = config.tech_stack or self._create_tech_stack(analysis, config)
        folder_structure = self._create_folder_structure(tech_stack)
        milestones = self._create_milestones(config.project_type)
        tasks = self._create_tasks(config.project_type, tech_stack)
        dependencies = self._create_dependencies(tech_stack)

        return ProjectPlan(
            project_name=config.project_name,
            project_type=config.project_type,
            description=config.description or config.project_name,
            tech_stack=tech_stack,
            folder_structure=folder_structure,
            milestones=milestones,
            tasks=tasks,
            dependencies=dependencies,
        )

    async def generate_code(self, plan: ProjectPlan, output_dir: str) -> list[str]:
        """Generate project code."""
        project_dir = Path(output_dir) / plan.project_name.lower().replace(" ", "_")
        project_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Create folder structure
        for directory in plan.folder_structure.directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)

        # Generate main application file
        main_content = self._generate_main_file(plan)
        main_path = project_dir / self._get_main_filename(plan.tech_stack.language)
        main_path.write_text(main_content)
        generated_files.append(str(main_path))

        # Generate requirements/package file
        req_content = self._generate_requirements(plan)
        req_path = project_dir / self._get_requirements_filename(plan.tech_stack.language)
        req_path.write_text(req_content)
        generated_files.append(str(req_path))

        # Generate config file
        config_content = self._generate_config_file(plan)
        config_path = project_dir / self._get_config_filename(plan.tech_stack.language)
        config_path.write_text(config_content)
        generated_files.append(str(config_path))

        # Generate README
        readme_content = self._generate_readme(plan)
        readme_path = project_dir / "README.md"
        readme_path.write_text(readme_content)
        generated_files.append(str(readme_path))

        # Generate .gitignore
        gitignore_content = self._generate_gitignore(plan)
        gitignore_path = project_dir / ".gitignore"
        gitignore_path.write_text(gitignore_content)
        generated_files.append(str(gitignore_path))

        # Generate tests
        if plan.tech_stack.language == "python":
            test_content = self._generate_python_tests(plan)
            test_path = project_dir / "tests" / "test_main.py"
            test_path.write_text(test_content)
            generated_files.append(str(test_path))

        # Generate Docker
        if plan.tech_stack.container == "docker":
            docker_content = self._generate_dockerfile(plan)
            docker_path = project_dir / "Dockerfile"
            docker_path.write_text(docker_content)
            generated_files.append(str(docker_path))

        # Generate CI
        ci_content = self._generate_ci_workflow(plan)
        ci_path = project_dir / ".github" / "workflows" / "ci.yml"
        ci_path.parent.mkdir(parents=True, exist_ok=True)
        ci_path.write_text(ci_content)
        generated_files.append(str(ci_path))

        return generated_files

    def _get_main_filename(self, language: str) -> str:
        """Get main filename by language."""
        filenames = {
            "python": "main.py",
            "typescript": "src/index.ts",
            "javascript": "src/index.js",
            "go": "cmd/main.go",
            "rust": "src/main.rs",
        }
        return filenames.get(language, "main.py")

    def _get_requirements_filename(self, language: str) -> str:
        """Get requirements filename by language."""
        filenames = {
            "python": "requirements.txt",
            "typescript": "package.json",
            "javascript": "package.json",
            "go": "go.mod",
            "rust": "Cargo.toml",
        }
        return filenames.get(language, "requirements.txt")

    def _get_config_filename(self, language: str) -> str:
        """Get config filename by language."""
        filenames = {
            "python": "config.py",
            "typescript": "tsconfig.json",
            "javascript": "jsconfig.json",
            "go": "config.yaml",
            "rust": "config.toml",
        }
        return filenames.get(language, "config.py")

    def _generate_main_file(self, plan: ProjectPlan) -> str:
        """Generate main application file."""
        language = plan.tech_stack.language

        if language == "python":
            return f'''"""Main application module for {plan.project_name}."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


app = FastAPI(title="{plan.project_name}", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to {plan.project_name}", "version": "0.1.0"}}


@app.post("/api/echo")
async def echo(data: dict):
    """Echo endpoint for testing."""
    return {{"echo": data}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        elif language == "typescript":
            return '''import express from "express";

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get("/health", (req, res) => {
  res.json({ status: "healthy", version: "0.1.0" });
});

app.get("/", (req, res) => {
  res.json({ message: "Welcome to the API", version: "0.1.0" });
});

app.post("/api/echo", (req, res) => {
  res.json({ echo: req.body });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${{PORT}}`);
});

export default app;
'''

        elif language == "go":
            return '''package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Version string `json:"version"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(HealthResponse{Status: "healthy", Version: "0.1.0"})
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"message": "Welcome", "version": "0.1.0"})
}

func main() {
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/", rootHandler)
	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
'''

        return "# Main application file"

    def _generate_requirements(self, plan: ProjectPlan) -> str:
        """Generate requirements file."""
        language = plan.tech_stack.language

        if language == "python":
            reqs = ["fastapi>=0.100.0", "uvicorn>=0.23.0", "pydantic>=2.0.0"]
            if plan.tech_stack.database:
                if "postgres" in plan.tech_stack.database:
                    reqs.append("asyncpg>=0.28.0")
                elif "mysql" in plan.tech_stack.database:
                    reqs.append("aiomysql>=0.2.0")
            reqs.extend(["pytest>=7.0.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.0.0"])
            return "\n".join(reqs) + "\n"

        elif language in ["typescript", "javascript"]:
            package = {
                "name": plan.project_name.lower().replace(" ", "-"),
                "version": "0.1.0",
                "scripts": {"start": "node src/index.js", "test": "jest"},
                "dependencies": {"express": "^4.18.0"},
                "devDependencies": {"jest": "^29.0.0", "@types/node": "^20.0.0"},
            }
            return json.dumps(package, indent=2)

        elif language == "go":
            return f'''module {plan.project_name.lower().replace(" ", "-")}

go 1.21
'''

        return ""

    def _generate_config_file(self, plan: ProjectPlan) -> str:
        """Generate configuration file."""
        if plan.tech_stack.language == "python":
            return f'''"""Configuration for {plan.project_name}."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "{plan.project_name}"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    api_version: str = "v1"

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "{plan.tech_stack.database or "sqlite"}:///./{plan.project_name.lower().replace(" ", "_")}.db"
    )

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"


settings = Settings()
'''

        elif plan.tech_stack.language == "go":
            return f'''server:
  host: "0.0.0.0"
  port: 8080

database:
  url: "{plan.tech_stack.database or "sqlite"}:///{plan.project_name.lower()}.db"
'''

        return ""

    def _generate_readme(self, plan: ProjectPlan) -> str:
        """Generate README.md."""
        tech = plan.tech_stack
        return f'''# {plan.project_name}

{plan.description}

## Tech Stack

- **Language**: {tech.language}
- **Framework**: {tech.framework or "N/A"}
- **Database**: {tech.database or "None"}

## Getting Started

### Prerequisites

- {tech.language} (latest version)
{"- Docker" if tech.container else ""}

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/{plan.project_name.lower().replace(" ", "-")}.git
cd {plan.project_name.lower().replace(" ", "-")}

# Install dependencies
{"pip install -r requirements.txt" if tech.language == "python" else "npm install" if tech.language in ["typescript", "javascript"] else ""}

# Run the application
{"python main.py" if tech.language == "python" else "go run cmd/main.go" if tech.language == "go" else "npm start"}
```

### Docker

```bash
# Build and run with Docker
docker build -t {plan.project_name.lower()} .
docker run -p 8000:8000 {plan.project_name.lower()}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | Root endpoint |
| POST | `/api/echo` | Echo endpoint |

## Testing

```bash
{"pytest tests/ -v" if tech.language == "python" else "npm test"}
```

## License

MIT
'''

    def _generate_gitignore(self, plan: ProjectPlan) -> str:
        """Generate .gitignore."""
        language = plan.tech_stack.language
        ignores = [
            "# Environment",
            ".env",
            ".env.local",
            ".env.*.local",
            "",
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            "dist/",
            "build/",
            "*.egg-info/",
            "",
            "# Node",
            "node_modules/",
            "npm-debug.log*",
            ".npm",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Database",
            "*.db",
            "*.sqlite",
        ]

        if plan.tech_stack.database and "postgres" in plan.tech_stack.database:
            ignores.extend(["", "# PostgreSQL", "*.sql"])

        return "\n".join(ignores) + "\n"

    def _generate_python_tests(self, plan: ProjectPlan) -> str:
        """Generate Python tests."""
        return f'''"""Tests for {plan.project_name}."""

import pytest
from fastapi.testclient import TestClient


class TestHealth:
    """Test health endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAPI:
    """Test API endpoints."""

    def test_echo(self, client):
        """Test echo endpoint."""
        response = client.post("/api/echo", json={{"test": "data"}})
        assert response.status_code == 200
        data = response.json()
        assert data["echo"]["test"] == "data"


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)
'''

    def _generate_dockerfile(self, plan: ProjectPlan) -> str:
        """Generate Dockerfile."""
        language = plan.tech_stack.language

        if language == "python":
            return '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

        elif language == "typescript":
            return '''FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["node", "dist/index.js"]
'''

        elif language == "go":
            return '''FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .
RUN go build -o main ./cmd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 8080

CMD ["./main"]
'''

        return '''FROM alpine:latest
WORKDIR /app
COPY . .
CMD ["echo", "Container started"]
'''

    def _generate_ci_workflow(self, plan: ProjectPlan) -> str:
        """Generate GitHub Actions CI workflow."""
        language = plan.tech_stack.language

        if language == "python":
            return '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Lint
        run: |
          pip install ruff
          ruff check .
'''

        elif language in ["typescript", "javascript"]:
            return '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build
'''

        elif language == "go":
            return '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: "1.21"

      - name: Test
        run: go test -v -race ./...

      - name: Build
        run: go build ./...
'''

        return '''name: CI

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Build step"
'''

    # ===== Main Generation =====

    async def generate(
        self,
        config: GenerationConfig,
        progress_callback=None,
    ) -> ProjectGeneration:
        """Generate complete project from configuration."""
        generation_id = str(uuid.uuid4())

        self._generation = ProjectGeneration(
            generation_id=generation_id,
            config=config,
            status=ProjectStatus.PLANNING,
        )

        try:
            # Phase 1: Planning
            self._generation.status = ProjectStatus.PLANNING
            self._generation.plan = await self.generate_plan(config)

            if progress_callback:
                await progress_callback(10, "Plan generated")

            # Phase 2: Generation
            self._generation.status = ProjectStatus.GENERATING
            output_dir = config.output_directory

            generated = await self.generate_code(self._generation.plan, output_dir)

            for i, file_path in enumerate(generated):
                self._generation.generated_files.append(
                    GeneratedFile(path=file_path, content="")
                )
                if progress_callback:
                    progress = 10 + int((i + 1) / len(generated) * 80)
                    await progress_callback(progress, f"Generated {Path(file_path).name}")

            # Phase 3: Complete
            self._generation.status = ProjectStatus.COMPLETED
            self._generation.completed_at = datetime.utcnow()
            self._generation.progress_percent = 100.0

            if progress_callback:
                await progress_callback(100, "Project generation complete")

        except Exception as e:
            self._generation.status = ProjectStatus.FAILED
            self._generation.errors.append(str(e))

        return self._generation
