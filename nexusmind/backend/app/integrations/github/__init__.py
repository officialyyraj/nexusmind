"""GitHub integration module."""

from app.integrations.github.github_client import GitHubClient
from app.integrations.github.github_service import GitHubService, get_github_service
from app.integrations.github.router import router
from app.integrations.github.schemas import (
    BranchCreateRequest,
    BranchInfo,
    CommitRequest,
    CommitInfo,
    FileContentResponse,
    GitHubOperation,
    GitHubOperationResponse,
    IssueCreateRequest,
    IssueInfo,
    IssueUpdateRequest,
    PullRequestCreateRequest,
    PullRequestInfo,
    PullRequest,
    PushRequest,
    PushResult,
    RepositoryCloneRequest,
    RepositoryInfo,
    RepositoryOpenRequest,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    TreeItem,
)

__all__ = [
    "GitHubClient",
    "GitHubService",
    "get_github_service",
    "router",
    # Schemas
    "BranchCreateRequest",
    "BranchInfo",
    "CommitRequest",
    "CommitInfo",
    "FileContentResponse",
    "GitHubOperation",
    "GitHubOperationResponse",
    "IssueCreateRequest",
    "IssueInfo",
    "IssueUpdateRequest",
    "PullRequestCreateRequest",
    "PullRequestInfo",
    "PullRequest",
    "PushRequest",
    "PushResult",
    "RepositoryCloneRequest",
    "RepositoryInfo",
    "RepositoryOpenRequest",
    "SearchRequest",
    "SearchResponse",
    "SearchResultItem",
    "TreeItem",
]
