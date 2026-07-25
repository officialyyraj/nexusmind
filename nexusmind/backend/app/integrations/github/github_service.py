"""GitHub service layer."""

from typing import Any

from app.integrations.github.github_client import GitHubClient
from app.integrations.github.schemas import (
    BranchCreateRequest,
    BranchInfo,
    CommitInfo,
    CommitRequest,
    FileContentResponse,
    GitHubOperation,
    GitHubOperationResponse,
    GitHubOperationResponse,
    IssueCreateRequest,
    IssueInfo,
    IssueUpdateRequest,
    PullRequestCreateRequest,
    PullRequestInfo,
    PullResult,
    PushRequest,
    PushResult,
    PullRequest,
    RepositoryCloneRequest,
    RepositoryInfo,
    RepositoryOpenRequest,
    SearchRequest,
    SearchResponse,
    TreeItem,
)


class GitHubService:
    """GitHub service for orchestrating operations."""

    def __init__(self, token: str | None = None):
        """Initialize GitHub service.
        
        Args:
            token: GitHub personal access token
        """
        self.client = GitHubClient(token=token)

    # ==================== Repository Operations ====================

    async def clone_repository(
        self,
        request: RepositoryCloneRequest,
    ) -> GitHubOperationResponse:
        """Clone a repository.
        
        Args:
            request: Clone request
            
        Returns:
            Operation response
        """
        try:
            path = self.client.clone_repository(
                repo_url=request.repo_url,
                local_path=request.local_path,
                branch=request.branch,
                depth=request.depth,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.CLONE,
                data={"path": path},
                message=f"Cloned to {path}",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.CLONE,
                error=str(e),
            )

    async def open_repository(
        self,
        request: RepositoryOpenRequest,
    ) -> GitHubOperationResponse:
        """Open an existing repository.
        
        Args:
            request: Open request
            
        Returns:
            Operation response
        """
        try:
            repo = self.client.open_repository(request.local_path)
            branch = repo.active_branch.name
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.OPEN,
                data={
                    "path": request.local_path,
                    "branch": branch,
                    "is_dirty": repo.is_dirty(),
                },
                message=f"Opened repository on branch '{branch}'",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.OPEN,
                error=str(e),
            )

    async def get_repository_info(
        self,
        repo_path: str,
    ) -> GitHubOperationResponse:
        """Get repository information.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Operation response with repository info
        """
        try:
            info = self.client.get_repository_info(repo_path)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.OPEN,
                data=info,
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.OPEN,
                error=str(e),
            )

    # ==================== Branch Operations ====================

    async def create_branch(
        self,
        request: BranchCreateRequest,
    ) -> GitHubOperationResponse:
        """Create a branch.
        
        Args:
            request: Branch creation request
            
        Returns:
            Operation response
        """
        try:
            branch = self.client.create_branch(
                repo_path=request.repo_path,
                branch_name=request.branch_name,
                from_branch=request.from_branch,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.CREATE_BRANCH,
                data=branch.model_dump(),
                message=f"Created branch '{request.branch_name}'",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.CREATE_BRANCH,
                error=str(e),
            )

    async def list_branches(
        self,
        repo_path: str,
    ) -> GitHubOperationResponse:
        """List all branches.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Operation response with branches
        """
        try:
            branches = self.client.list_branches(repo_path)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.OPEN,
                data={"branches": [b.model_dump() for b in branches]},
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.OPEN,
                error=str(e),
            )

    # ==================== Commit Operations ====================

    async def commit_changes(
        self,
        request: CommitRequest,
    ) -> GitHubOperationResponse:
        """Commit changes.
        
        Args:
            request: Commit request
            
        Returns:
            Operation response
        """
        try:
            commit = self.client.commit_changes(
                repo_path=request.repo_path,
                message=request.message,
                files=request.files,
                author_name=request.author_name,
                author_email=request.author_email,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.COMMIT,
                data=commit.model_dump(),
                message=f"Committed with SHA: {commit.sha[:8]}",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.COMMIT,
                error=str(e),
            )

    # ==================== Remote Operations ====================

    async def push_changes(
        self,
        request: PushRequest,
    ) -> GitHubOperationResponse:
        """Push changes.
        
        Args:
            request: Push request
            
        Returns:
            Operation response
        """
        try:
            result = self.client.push_changes(
                repo_path=request.repo_path,
                remote=request.remote,
                branch=request.branch,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.PUSH,
                data=result,
                message=f"Pushed {result['pushed_commits']} commits to {request.remote}",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.PUSH,
                error=str(e),
            )

    async def pull_changes(
        self,
        request: PullRequest,
    ) -> GitHubOperationResponse:
        """Pull changes.
        
        Args:
            request: Pull request
            
        Returns:
            Operation response
        """
        try:
            result = self.client.pull_changes(
                repo_path=request.repo_path,
                remote=request.remote,
                branch=request.branch,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.PULL,
                data=result,
                message=f"Pulled {result['files_changed']} files",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.PULL,
                error=str(e),
            )

    # ==================== Pull Request Operations ====================

    async def get_pull_requests(
        self,
        repo_url: str,
        state: str = "open",
    ) -> GitHubOperationResponse:
        """Get pull requests.
        
        Args:
            repo_url: Repository URL
            state: PR state
            
        Returns:
            Operation response with PRs
        """
        try:
            prs = self.client.get_pull_requests(repo_url, state)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.READ_ISSUES,
                data={"pull_requests": [pr.model_dump() for pr in prs]},
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.READ_ISSUES,
                error=str(e),
            )

    async def create_pull_request(
        self,
        request: PullRequestCreateRequest,
    ) -> GitHubOperationResponse:
        """Create a pull request.
        
        Args:
            request: PR creation request
            
        Returns:
            Operation response
        """
        try:
            pr = self.client.create_pull_request(
                repo_path=request.repo_path,
                request=request,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.CREATE_PR,
                data=pr.model_dump(),
                message=f"Created PR #{pr.number}: {pr.title}",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.CREATE_PR,
                error=str(e),
            )

    # ==================== Issue Operations ====================

    async def get_issues(
        self,
        repo_url: str,
        state: str = "open",
        labels: list[str] | None = None,
    ) -> GitHubOperationResponse:
        """Get issues.
        
        Args:
            repo_url: Repository URL
            state: Issue state
            labels: Filter by labels
            
        Returns:
            Operation response with issues
        """
        try:
            issues = self.client.get_issues(repo_url, state, labels)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.READ_ISSUES,
                data={"issues": [issue.model_dump() for issue in issues]},
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.READ_ISSUES,
                error=str(e),
            )

    async def create_issue(
        self,
        request: IssueCreateRequest,
    ) -> GitHubOperationResponse:
        """Create an issue.
        
        Args:
            request: Issue creation request
            
        Returns:
            Operation response
        """
        try:
            issue = self.client.create_issue(
                repo_url=request.repo_url,
                title=request.title,
                body=request.body,
                labels=request.labels,
                assignees=request.assignees,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.CREATE_ISSUE,
                data=issue.model_dump(),
                message=f"Created issue #{issue.number}: {issue.title}",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.CREATE_ISSUE,
                error=str(e),
            )

    async def update_issue(
        self,
        repo_url: str,
        issue_number: int,
        request: IssueUpdateRequest,
    ) -> GitHubOperationResponse:
        """Update an issue.
        
        Args:
            repo_url: Repository URL
            issue_number: Issue number
            request: Update request
            
        Returns:
            Operation response
        """
        try:
            issue = self.client.update_issue(
                repo_url=repo_url,
                issue_number=issue_number,
                request=request,
            )
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.CREATE_ISSUE,
                data=issue.model_dump(),
                message=f"Updated issue #{issue.number}",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.CREATE_ISSUE,
                error=str(e),
            )

    # ==================== Tree Operations ====================

    async def get_tree(
        self,
        repo_path: str,
        path: str = "/",
        recursive: bool = False,
    ) -> GitHubOperationResponse:
        """Get repository tree.
        
        Args:
            repo_path: Path to repository
            path: Path within repository
            recursive: Include subdirectories
            
        Returns:
            Operation response with tree
        """
        try:
            tree = self.client.get_tree(repo_path, path, recursive)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.READ_TREE,
                data={"tree": [item.model_dump() for item in tree]},
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.READ_TREE,
                error=str(e),
            )

    # ==================== File Operations ====================

    async def read_file(
        self,
        repo_path: str,
        file_path: str,
        ref: str | None = None,
    ) -> GitHubOperationResponse:
        """Read file content.
        
        Args:
            repo_path: Path to repository
            file_path: Path to file
            ref: Branch or commit SHA
            
        Returns:
            Operation response with file content
        """
        try:
            content = self.client.read_file(repo_path, file_path, ref)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.READ_FILE,
                data=content.model_dump(),
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.READ_FILE,
                error=str(e),
            )

    # ==================== Search Operations ====================

    async def search(
        self,
        request: SearchRequest,
    ) -> GitHubOperationResponse:
        """Search repository.
        
        Args:
            request: Search request
            
        Returns:
            Operation response with search results
        """
        try:
            results = self.client.search(request)
            
            return GitHubOperationResponse(
                success=True,
                operation=GitHubOperation.SEARCH,
                data=results.model_dump(),
                message=f"Found {results.total} results",
            )
        except Exception as e:
            return GitHubOperationResponse(
                success=False,
                operation=GitHubOperation.SEARCH,
                error=str(e),
            )


# Global service instance
_github_service: GitHubService | None = None


def get_github_service(token: str | None = None) -> GitHubService:
    """Get GitHub service instance.
    
    Args:
        token: GitHub token
        
    Returns:
        GitHubService instance
    """
    global _github_service
    if _github_service is None:
        _github_service = GitHubService(token=token)
    return _github_service
