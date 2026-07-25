"""GitHub integration router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query

from app.integrations.github.github_service import GitHubService, get_github_service
from app.integrations.github.schemas import (
    BranchCreateRequest,
    CommitRequest,
    FileContentResponse,
    GitHubOperationResponse,
    IssueCreateRequest,
    IssueInfo,
    IssueUpdateRequest,
    PullRequestCreateRequest,
    PullRequestInfo,
    PullRequest,
    PushRequest,
    RepositoryCloneRequest,
    RepositoryOpenRequest,
    SearchRequest,
    SearchResponse,
    TreeItem,
)


router = APIRouter(prefix="/github", tags=["GitHub Integration"])


def get_service(
    authorization: Annotated[str | None, Header()] = None,
) -> GitHubService:
    """Get GitHub service with token from Authorization header."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    return get_github_service(token=token)


# ==================== Repository Endpoints ====================


@router.post("/clone", response_model=GitHubOperationResponse)
async def clone_repository(
    request: RepositoryCloneRequest,
    service: GitHubService = Depends(get_service),
):
    """Clone a GitHub repository.
    
    Args:
        request: Clone request with repo URL and local path
        service: GitHub service
        
    Returns:
        Operation response with cloned path
    """
    return await service.clone_repository(request)


@router.post("/open", response_model=GitHubOperationResponse)
async def open_repository(
    request: RepositoryOpenRequest,
    service: GitHubService = Depends(get_service),
):
    """Open an existing repository.
    
    Args:
        request: Open request with local path
        service: GitHub service
        
    Returns:
        Operation response with repository info
    """
    return await service.open_repository(request)


@router.get("/repo/{repo_path:path}/info", response_model=GitHubOperationResponse)
async def get_repository_info(
    repo_path: str = Path(..., description="Path to repository"),
    service: GitHubService = Depends(get_service),
):
    """Get repository information.
    
    Args:
        repo_path: Path to repository
        service: GitHub service
        
    Returns:
        Operation response with repository info
    """
    return await service.get_repository_info(repo_path)


# ==================== Branch Endpoints ====================


@router.post("/branch/create", response_model=GitHubOperationResponse)
async def create_branch(
    request: BranchCreateRequest,
    service: GitHubService = Depends(get_service),
):
    """Create a new branch.
    
    Args:
        request: Branch creation request
        service: GitHub service
        
    Returns:
        Operation response with branch info
    """
    return await service.create_branch(request)


@router.get("/repo/{repo_path:path}/branches", response_model=GitHubOperationResponse)
async def list_branches(
    repo_path: str = Path(..., description="Path to repository"),
    service: GitHubService = Depends(get_service),
):
    """List all branches in repository.
    
    Args:
        repo_path: Path to repository
        service: GitHub service
        
    Returns:
        Operation response with branches
    """
    return await service.list_branches(repo_path)


# ==================== Commit Endpoints ====================


@router.post("/commit", response_model=GitHubOperationResponse)
async def commit_changes(
    request: CommitRequest,
    service: GitHubService = Depends(get_service),
):
    """Commit changes to repository.
    
    Args:
        request: Commit request
        service: GitHub service
        
    Returns:
        Operation response with commit info
    """
    return await service.commit_changes(request)


# ==================== Remote Operation Endpoints ====================


@router.post("/push", response_model=GitHubOperationResponse)
async def push_changes(
    request: PushRequest,
    service: GitHubService = Depends(get_service),
):
    """Push changes to remote.
    
    Args:
        request: Push request
        service: GitHub service
        
    Returns:
        Operation response with push result
    """
    return await service.push_changes(request)


@router.post("/pull", response_model=GitHubOperationResponse)
async def pull_changes(
    request: PullRequest,
    service: GitHubService = Depends(get_service),
):
    """Pull changes from remote.
    
    Args:
        request: Pull request
        service: GitHub service
        
    Returns:
        Operation response with pull result
    """
    return await service.pull_changes(request)


# ==================== Pull Request Endpoints ====================


@router.get("/repo/{repo_url}/pulls", response_model=GitHubOperationResponse)
async def get_pull_requests(
    repo_url: str = Path(..., description="Repository URL"),
    state: str = Query("open", description="PR state (open, closed, all)"),
    service: GitHubService = Depends(get_service),
):
    """Get pull requests for repository.
    
    Args:
        repo_url: Repository URL
        state: PR state filter
        service: GitHub service
        
    Returns:
        Operation response with PRs
    """
    return await service.get_pull_requests(repo_url, state)


@router.post("/pull-request/create", response_model=GitHubOperationResponse)
async def create_pull_request(
    request: PullRequestCreateRequest,
    service: GitHubService = Depends(get_service),
):
    """Create a pull request.
    
    Args:
        request: PR creation request
        service: GitHub service
        
    Returns:
        Operation response with created PR
    """
    return await service.create_pull_request(request)


# ==================== Issue Endpoints ====================


@router.get("/repo/{repo_url}/issues", response_model=GitHubOperationResponse)
async def get_issues(
    repo_url: str = Path(..., description="Repository URL"),
    state: str = Query("open", description="Issue state (open, closed, all)"),
    labels: str | None = Query(None, description="Comma-separated labels"),
    service: GitHubService = Depends(get_service),
):
    """Get issues for repository.
    
    Args:
        repo_url: Repository URL
        state: Issue state filter
        labels: Label filter (comma-separated)
        service: GitHub service
        
    Returns:
        Operation response with issues
    """
    label_list = labels.split(",") if labels else None
    return await service.get_issues(repo_url, state, label_list)


@router.post("/issue/create", response_model=GitHubOperationResponse)
async def create_issue(
    request: IssueCreateRequest,
    service: GitHubService = Depends(get_service),
):
    """Create an issue.
    
    Args:
        request: Issue creation request
        service: GitHub service
        
    Returns:
        Operation response with created issue
    """
    return await service.create_issue(request)


@router.patch("/repo/{repo_url}/issues/{issue_number}", response_model=GitHubOperationResponse)
async def update_issue(
    repo_url: str = Path(..., description="Repository URL"),
    issue_number: int = Path(..., description="Issue number"),
    request: IssueUpdateRequest = ...,
    service: GitHubService = Depends(get_service),
):
    """Update an issue.
    
    Args:
        repo_url: Repository URL
        issue_number: Issue number
        request: Update request
        service: GitHub service
        
    Returns:
        Operation response with updated issue
    """
    return await service.update_issue(repo_url, issue_number, request)


# ==================== Tree Endpoints ====================


@router.get("/repo/{repo_path:path}/tree", response_model=GitHubOperationResponse)
async def get_tree(
    repo_path: str = Path(..., description="Path to repository"),
    path: str = Query("/", description="Path within repository"),
    recursive: bool = Query(False, description="Include subdirectories"),
    service: GitHubService = Depends(get_service),
):
    """Get repository tree structure.
    
    Args:
        repo_path: Path to repository
        path: Path within repository
        recursive: Include subdirectories
        service: GitHub service
        
    Returns:
        Operation response with tree structure
    """
    return await service.get_tree(repo_path, path, recursive)


# ==================== File Endpoints ====================


@router.get("/repo/{repo_path:path}/file/{file_path:path}", response_model=GitHubOperationResponse)
async def read_file(
    repo_path: str = Path(..., description="Path to repository"),
    file_path: str = Path(..., description="Path to file"),
    ref: str | None = Query(None, description="Branch or commit SHA"),
    service: GitHubService = Depends(get_service),
):
    """Read file content.
    
    Args:
        repo_path: Path to repository
        file_path: Path to file
        ref: Branch or commit SHA
        service: GitHub service
        
    Returns:
        Operation response with file content
    """
    return await service.read_file(repo_path, file_path, ref)


# ==================== Search Endpoints ====================


@router.post("/search", response_model=GitHubOperationResponse)
async def search(
    request: SearchRequest,
    service: GitHubService = Depends(get_service),
):
    """Search repository.
    
    Args:
        request: Search request
        service: GitHub service
        
    Returns:
        Operation response with search results
    """
    return await service.search(request)
