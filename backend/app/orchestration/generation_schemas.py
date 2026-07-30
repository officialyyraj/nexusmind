"""Project generation schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project generation status."""

    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectType(str, Enum):
    """Type of project to generate."""

    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    FULLSTACK_APP = "fullstack_app"
    DATA_PIPELINE = "data_pipeline"
    CUSTOM = "custom"


class TechStack(BaseModel):
    """Technology stack specification."""

    language: str = Field(..., description="Primary language")
    framework: str | None = Field(None, description="Framework")
    backend: str | None = Field(None, description="Backend framework")
    frontend: str | None = Field(None, description="Frontend framework")
    database: str | None = Field(None, description="Database")
    cache: str | None = Field(None, description="Cache")
    queue: str | None = Field(None, description="Message queue")
    container: str = "docker"
    orchestration: str | None = Field(None, description="Orchestration (k8s, docker-compose)")
    testing: list[str] = Field(default_factory=list)
    ci_cd: list[str] = Field(default_factory=list)
    cloud: str | None = Field(None, description="Cloud provider")


class FolderStructure(BaseModel):
    """Folder structure specification."""

    root: str = Field(..., description="Project root name")
    directories: list[str] = Field(default_factory=list)
    files: list[dict[str, str]] = Field(
        default_factory=list,
        description="Files to create: [{path, description}]"
    )
    hidden_files: list[str] = Field(
        default_factory=list,
        description="Hidden files like .gitignore, .env.example"
    )


class Milestone(BaseModel):
    """Project milestone."""

    id: str
    name: str
    description: str
    tasks: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    estimated_hours: float = 0.0


class Task(BaseModel):
    """Individual task."""

    id: str
    title: str
    description: str
    priority: int = Field(1, ge=1, le=5, description="Priority (1=highest)")
    estimated_hours: float = 0.0
    assigned_agent: str | None = Field(None, description="Assigned agent type")
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.PLANNING


class Dependency(BaseModel):
    """Project dependency."""

    package: str
    version: str
    type: str = Field("runtime", description="runtime, dev, test")


class GeneratedFile(BaseModel):
    """A generated file."""

    path: str
    content: str
    language: str | None = None
    generated_by: str | None = None


class ProjectPlan(BaseModel):
    """Complete project plan."""

    project_name: str
    project_type: ProjectType
    description: str
    tech_stack: TechStack
    folder_structure: FolderStructure
    milestones: list[Milestone] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class GenerationConfig(BaseModel):
    """Configuration for project generation."""

    project_name: str
    project_type: ProjectType = ProjectType.WEB_APP
    description: str = ""
    tech_stack: TechStack | None = None
    auto_assign_agents: bool = True
    generate_docker: bool = True
    generate_readme: bool = True
    generate_tests: bool = True
    generate_ci: bool = True
    output_directory: str = "/tmp/generated_projects"


class ProjectGeneration(BaseModel):
    """Complete project generation state."""

    generation_id: str
    config: GenerationConfig
    plan: ProjectPlan | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    current_task: str | None = None
    generated_files: list[GeneratedFile] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    progress_percent: float = 0.0


class CodeTemplate(BaseModel):
    """Code template for generation."""

    name: str
    language: str
    template: str
    placeholders: dict[str, str] = Field(default_factory=dict)
