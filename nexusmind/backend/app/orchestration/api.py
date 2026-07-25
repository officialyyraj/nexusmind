"""REST API for project generation."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.orchestration.generation_schemas import (
    GenerationConfig,
    ProjectGeneration,
    ProjectPlan,
    ProjectStatus,
)
from app.orchestration.project_generator import ProjectGenerator

router = APIRouter(prefix="/api/v1/projects", tags=["project-generation"])

# In-memory storage for generations
_generations: dict[str, ProjectGeneration] = {}

# Shared generator instance
_generator = ProjectGenerator()


@router.post("/generate", response_model=ProjectGeneration)
async def generate_project(config: GenerationConfig) -> ProjectGeneration:
    """Generate a new project from configuration.
    
    Args:
        config: Project generation configuration
        
    Returns:
        Generation result with status and generated files
    """
    generation = await _generator.generate(config)
    
    _generations[generation.generation_id] = generation
    
    return generation


@router.post("/generate/stream")
async def generate_project_stream(config: GenerationConfig):
    """Generate a project with streaming progress.
    
    Args:
        config: Project generation configuration
        
    Returns:
        Server-sent events with progress updates
    """
    generation_id = str(uuid.uuid4())
    
    async def event_generator():
        try:
            # Send initial status
            yield {
                "event": "status",
                "data": json.dumps({"status": "planning", "progress": 0}),
            }
            
            # Generate plan
            plan = await _generator.generate_plan(config)
            yield {
                "event": "plan",
                "data": json.dumps(plan.model_dump()),
            }
            
            yield {
                "event": "status",
                "data": json.dumps({"status": "generating", "progress": 10}),
            }
            
            # Generate files
            output_dir = config.output_directory
            project_dir = Path(output_dir) / plan.project_name.lower().replace(" ", "_")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            files = await _generator.generate_code(plan, output_dir)
            
            for i, file_path in enumerate(files):
                progress = 10 + int((i + 1) / len(files) * 80)
                yield {
                    "event": "file",
                    "data": json.dumps({
                        "path": file_path,
                        "progress": progress,
                    }),
                }
            
            # Complete
            yield {
                "event": "status",
                "data": json.dumps({"status": "completed", "progress": 100}),
            }
            
            yield {
                "event": "complete",
                "data": json.dumps({
                    "generation_id": generation_id,
                    "project_name": plan.project_name,
                    "output_directory": str(project_dir),
                    "files_generated": len(files),
                }),
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }
    
    return EventSourceResponse(event_generator())


@router.get("/{generation_id}")
async def get_generation(generation_id: str) -> ProjectGeneration:
    """Get generation by ID.
    
    Args:
        generation_id: Generation ID
        
    Returns:
        Generation details
    """
    if generation_id not in _generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    return _generations[generation_id]


@router.get("/{generation_id}/plan")
async def get_plan(generation_id: str) -> ProjectPlan:
    """Get project plan from a generation.
    
    Args:
        generation_id: Generation ID
        
    Returns:
        Project plan
    """
    if generation_id not in _generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = _generations[generation_id]
    if not generation.plan:
        raise HTTPException(status_code=404, detail="Plan not available")
    
    return generation.plan


@router.get("/{generation_id}/files")
async def list_generated_files(generation_id: str) -> list[dict[str, Any]]:
    """List generated files from a generation.
    
    Args:
        generation_id: Generation ID
        
    Returns:
        List of generated files with paths
    """
    if generation_id not in _generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = _generations[generation_id]
    return [
        {"path": f.path, "exists": Path(f.path).exists()}
        for f in generation.generated_files
    ]


@router.get("/{generation_id}/files/{file_path:path}")
async def get_file_content(generation_id: str, file_path: str) -> dict[str, Any]:
    """Get content of a generated file.
    
    Args:
        generation_id: Generation ID
        file_path: File path
        
    Returns:
        File content
    """
    if generation_id not in _generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    content = path.read_text()
    return {
        "path": str(path),
        "content": content,
        "language": _detect_language(path),
        "size": len(content),
    }


@router.get("/")
async def list_generations(
    status: ProjectStatus | None = None,
    limit: int = 20,
) -> list[ProjectGeneration]:
    """List all generations.
    
    Args:
        status: Filter by status
        limit: Max results
        
    Returns:
        List of generations
    """
    generations = list(_generations.values())
    
    if status:
        generations = [g for g in generations if g.status == status]
    
    return generations[-limit:][::-1]


@router.post("/plan")
async def create_plan(config: GenerationConfig) -> ProjectPlan:
    """Create a project plan without generating files.
    
    Args:
        config: Project generation configuration
        
    Returns:
        Generated project plan
    """
    return await _generator.generate_plan(config)


@router.delete("/{generation_id}")
async def delete_generation(generation_id: str) -> dict[str, str]:
    """Delete a generation and its files.
    
    Args:
        generation_id: Generation ID
        
    Returns:
        Success message
    """
    if generation_id not in _generations:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation = _generations[generation_id]
    
    # Delete generated files
    for file in generation.generated_files:
        path = Path(file.path)
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
    
    # Remove from storage
    del _generations[generation_id]
    
    return {"status": "deleted", "generation_id": generation_id}


def _detect_language(path: Path) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".ts": "typescript",
        ".js": "javascript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".dockerfile": "dockerfile",
    }
    return ext_map.get(path.suffix.lower(), "text")
