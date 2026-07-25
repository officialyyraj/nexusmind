"""GitHub integration schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GitHubOperation(str, Enum):
    """GitHub operation types."""

    CLONE = "clone"
    OPEN = "open"
    CREATE_BRANCH = "create_branch"
    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    CREATE_PR = "create_pr"
    READ_ISSUES = "read_issues"
    CREATE_ISSUE = "create_issue"
    READ_TREE = "read_tree"
    READ_FILE = "read_file"
    SEARCH = "search"


# ==================== Repository Schemas ====================


class RepositoryCloneRequest(BaseModel):
    """Request to clone a repository."""

    repo_url: str = Field(..., description="GitHub repository URL (e.g., https://github.com/owner/repo)")
    local_path: str = Field(..., description="Local path to clone to")
    branch: str | None = Field(None, description="Branch to clone (default: main)")
    depth: int | None = Field(None, description="Clone depth (None for full clone)")


class RepositoryOpenRequest(BaseModel):
    """Request to open an existing repository."""

    local_path: str = Field(..., description="Path to existing repository")


class RepositoryInfo(BaseModel):
    """Repository information."""

    name: str
    owner: str
    full_name: str
    description: str | None
    default_branch: str
    url: str
    clone_url: str
    language: str | None
    stars: int
    forks: int
    open_issues: int
    created_at: datetime
    updated_at: datetime


# ==================== Branch Schemas ====================


class BranchCreateRequest(BaseModel):
    """Request to create a branch."""

    repo_path: str = Field(..., description="Path to repository")
    branch_name: str = Field(..., description="Name for new branch")
    from_branch: str | None = Field(None, description="Source branch (default: current)")


class BranchInfo(BaseModel):
    """Branch information."""

    name: str
    commit_sha: str
    is_protected: bool
    is_default: bool


# ==================== Commit Schemas ====================


class CommitRequest(BaseModel):
    """Request to commit changes."""

    repo_path: str = Field(..., description="Path to repository")
    message: str = Field(..., description="Commit message")
    files: list[str] = Field(..., description="Files to commit (use '.' for all)")
    author_name: str | None = Field(None, description="Author name")
    author_email: str | None = Field(None, description="Author email")


class CommitInfo(BaseModel):
    """Commit information."""

    sha: str
    message: str
    author_name: str
    author_email: str
    author_date: datetime
    committer_name: str
    committer_email: str
    committer_date: datetime


# ==================== Push/Pull Schemas ====================


class PushRequest(BaseModel):
    """Request to push changes."""

    repo_path: str = Field(..., description="Path to repository")
    remote: str = Field("origin", description="Remote name")
    branch: str | None = Field(None, description="Branch to push (default: current)")


class PullRequest(BaseModel):
    """Request to pull changes."""

    repo_path: str = Field(..., description="Path to repository")
    remote: str = Field("origin", description="Remote name")
    branch: str | None = Field(None, description="Branch to pull (default: current)")


class PushResult(BaseModel):
    """Result of push operation."""

    success: bool
    pushed_commits: int
    branch: str


class PullResult(BaseModel):
    """Result of pull operation."""

    success: bool
    files_changed: int
    insertions: int
    deletions: int


# ==================== Pull Request Schemas ====================


class PullRequestCreateRequest(BaseModel):
    """Request to create a pull request."""

    repo_path: str = Field(..., description="Path to repository")
    title: str = Field(..., description="PR title")
    body: str | None = Field(None, description="PR description")
    head_branch: str = Field(..., description="Source branch")
    base_branch: str = Field("main", description="Target branch")
    draft: bool = Field(False, description="Create as draft PR")


class PullRequestInfo(BaseModel):
    """Pull request information."""

    number: int
    title: str
    body: str | None
    state: str
    draft: bool
    user: str
    head_branch: str
    base_branch: str
    html_url: str
    created_at: datetime
    updated_at: datetime


# ==================== Issue Schemas ====================


class IssueCreateRequest(BaseModel):
    """Request to create an issue."""

    repo_url: str = Field(..., description="Repository URL or local path")
    title: str = Field(..., description="Issue title")
    body: str | None = Field(None, description="Issue body")
    labels: list[str] = Field(default_factory=list, description="Issue labels")
    assignees: list[str] = Field(default_factory=list, description="Issue assignees")


class IssueUpdateRequest(BaseModel):
    """Request to update an issue."""

    title: str | None = None
    body: str | None = None
    state: str | None = Field(None, description="State: 'open' or 'closed'")
    labels: list[str] | None = None
    assignees: list[str] | None = None


class IssueInfo(BaseModel):
    """Issue information."""

    number: int
    title: str
    body: str | None
    state: str
    user: str
    labels: list[str]
    assignees: list[str]
    comments: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    html_url: str


# ==================== Repository Tree Schemas ====================


class TreeItem(BaseModel):
    """A file or directory in repository tree."""

    path: str
    type: str  # "blob" for file, "tree" for directory
    size: int | None
    sha: str


class TreeRequest(BaseModel):
    """Request to read repository tree."""

    repo_path: str = Field(..., description="Path to repository")
    path: str = Field("/", description="Path within repository")
    recursive: bool = Field(False, description="Include subdirectories")


# ==================== File Content Schemas ====================


class FileReadRequest(BaseModel):
    """Request to read file content."""

    repo_path: str = Field(..., description="Path to repository")
    file_path: str = Field(..., description="Path to file within repository")
    ref: str | None = Field(None, description="Branch or commit SHA")


class FileContentResponse(BaseModel):
    """Response with file content."""

    path: str
    content: str
    encoding: str
    size: int
    sha: str
    type: str  # "file" or "symlink" or "submodule"


class FileCreateRequest(BaseModel):
    """Request to create or update a file."""

    repo_path: str = Field(..., description="Path to repository")
    file_path: str = Field(..., description="Path to file")
    content: str = Field(..., description="File content")
    message: str = Field(..., description="Commit message")
    branch: str | None = Field(None, description="Branch to commit to")


# ==================== Search Schemas ====================


class SearchRequest(BaseModel):
    """Request to search repository."""

    repo_path: str = Field(..., description="Path to repository")
    query: str = Field(..., description="Search query")
    search_type: str = Field("code", description="Type: 'code', 'issues', 'commits'")
    path: str | None = Field(None, description="Limit to path")


class SearchResultItem(BaseModel):
    """A single search result item."""

    type: str
    path: str | None
    name: str
    sha: str
    url: str | None
    score: float


class SearchResponse(BaseModel):
    """Search response."""

    total: int
    results: list[SearchResultItem]


# ==================== Generic Response ====================


class GitHubOperationResponse(BaseModel):
    """Generic GitHub operation response."""

    success: bool
    operation: GitHubOperation
    data: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None
