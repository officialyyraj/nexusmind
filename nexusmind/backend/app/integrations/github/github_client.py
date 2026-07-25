"""GitHub client using GitPython and GitHub REST API."""

import base64
import os
import re
from pathlib import Path
from typing import Any

import git
import httpx
from git import Repo

from app.integrations.github.schemas import (
    BranchInfo,
    CommitInfo,
    FileContentResponse,
    IssueInfo,
    IssueUpdateRequest,
    PullRequestCreateRequest,
    PullRequestInfo,
    RepositoryInfo,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    TreeItem,
)


class GitHubClient:
    """GitHub client for repository operations."""

    GITHUB_API_URL = "https://api.github.com"

    def __init__(self, token: str | None = None):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token or GitHub App token
        """
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse GitHub URL to get owner and repo.
        
        Args:
            url: GitHub URL (https://github.com/owner/repo or owner/repo)
            
        Returns:
            Tuple of (owner, repo)
        """
        # Handle URLs like https://github.com/owner/repo
        match = re.match(r"github\.com[/:]([^/]+)/([^/.]+)", url)
        if match:
            return match.group(1), match.group(2)
        
        # Handle short form owner/repo
        if "/" in url:
            parts = url.split("/")
            return parts[0], parts[1]
        
        raise ValueError(f"Invalid GitHub URL: {url}")

    # ==================== Repository Operations ====================

    def clone_repository(
        self,
        repo_url: str,
        local_path: str,
        branch: str | None = None,
        depth: int | None = None,
    ) -> str:
        """Clone a GitHub repository.
        
        Args:
            repo_url: Repository URL
            local_path: Local path to clone to
            branch: Branch to clone (default: default branch)
            depth: Clone depth (None for full clone)
            
        Returns:
            Path to cloned repository
        """
        kwargs = {}
        if branch:
            kwargs["branch"] = branch
        if depth:
            kwargs["depth"] = depth
        
        repo = git.Repo.clone_from(repo_url, local_path, **kwargs)
        return str(repo.working_dir)

    def open_repository(self, local_path: str) -> Repo:
        """Open an existing repository.
        
        Args:
            local_path: Path to repository
            
        Returns:
            GitPython Repo object
        """
        if not os.path.exists(local_path):
            raise ValueError(f"Repository not found at: {local_path}")
        
        try:
            return Repo(local_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a valid git repository: {local_path}")

    def get_repository_info(self, repo_path: str) -> dict[str, Any]:
        """Get repository information.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Repository information dict
        """
        repo = self.open_repository(repo_path)
        
        # Try to get remote URL
        remote_url = None
        if repo.remotes:
            remote_url = repo.remotes.origin.url
        
        # Parse owner/repo from remote URL
        owner, repo_name = self._parse_repo_url(remote_url or repo_path)
        
        return {
            "name": repo_name,
            "owner": owner,
            "full_name": f"{owner}/{repo_name}",
            "description": None,
            "default_branch": repo.active_branch.name,
            "url": remote_url or "",
            "clone_url": remote_url or "",
            "language": None,
            "stars": 0,
            "forks": 0,
            "open_issues": 0,
        }

    def get_current_branch(self, repo_path: str) -> str:
        """Get current branch name.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Current branch name
        """
        repo = self.open_repository(repo_path)
        return repo.active_branch.name

    # ==================== Branch Operations ====================

    def create_branch(
        self,
        repo_path: str,
        branch_name: str,
        from_branch: str | None = None,
    ) -> BranchInfo:
        """Create a new branch.
        
        Args:
            repo_path: Path to repository
            branch_name: Name for new branch
            from_branch: Source branch (default: current branch)
            
        Returns:
            BranchInfo object
        """
        repo = self.open_repository(repo_path)
        
        if from_branch is None:
            from_branch = repo.active_branch.name
        
        # Get the commit to branch from
        ref = repo.refs[from_branch]
        
        # Create new branch
        new_branch = repo.create_head(branch_name, ref)
        new_branch.checkout()
        
        return BranchInfo(
            name=branch_name,
            commit_sha=ref.commit.hexsha,
            is_protected=False,
            is_default=False,
        )

    def list_branches(self, repo_path: str) -> list[BranchInfo]:
        """List all branches.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of BranchInfo objects
        """
        repo = self.open_repository(repo_path)
        current = repo.active_branch.name
        
        branches = []
        for ref in repo.refs:
            if isinstance(ref, git.Head):
                branches.append(BranchInfo(
                    name=ref.name,
                    commit_sha=ref.commit.hexsha,
                    is_protected=False,
                    is_default=(ref.name == current),
                ))
        
        return branches

    # ==================== Commit Operations ====================

    def commit_changes(
        self,
        repo_path: str,
        message: str,
        files: list[str] = None,
        author_name: str | None = None,
        author_email: str | None = None,
    ) -> CommitInfo:
        """Commit changes.
        
        Args:
            repo_path: Path to repository
            message: Commit message
            files: Files to commit ('.' for all)
            author_name: Author name
            author_email: Author email
            
        Returns:
            CommitInfo object
        """
        repo = self.open_repository(repo_path)
        
        # Stage files
        if files is None or files == ["."]:
            repo.index.add("*")
        else:
            for file in files:
                repo.index.add(file)
        
        if not repo.index.diff("HEAD") and not repo.untracked_files:
            raise ValueError("No changes to commit")
        
        # Set author if provided
        kwargs = {"message": message}
        if author_name:
            kwargs["author"] = git.Actor(author_name, author_email or "")
        
        # Commit
        commit = repo.index.commit(**kwargs)
        
        return CommitInfo(
            sha=commit.hexsha,
            message=commit.message,
            author_name=commit.author.name,
            author_email=commit.author.email,
            author_date=commit.authored_datetime,
            committer_name=commit.committer.name,
            committer_email=commit.committer.email,
            committer_date=commit.committed_datetime,
        )

    # ==================== Remote Operations ====================

    def push_changes(
        self,
        repo_path: str,
        remote: str = "origin",
        branch: str | None = None,
    ) -> dict[str, Any]:
        """Push changes to remote.
        
        Args:
            repo_path: Path to repository
            remote: Remote name
            branch: Branch to push (default: current)
            
        Returns:
            Push result dict
        """
        repo = self.open_repository(repo_path)
        
        if branch is None:
            branch = repo.active_branch.name
        
        origin = repo.remote(remote)
        
        # Count commits being pushed
        local_branch = repo.refs[branch]
        remote_branch = origin.refs[branch] if branch in [r.name for r in origin.refs] else None
        
        if remote_branch:
            commits_ahead = len(list(repo.iter_commits(
                f"{remote_branch.path}..{local_branch.path}"
            )))
        else:
            commits_ahead = len(list(repo.iter_commits(f"HEAD")))
        
        # Push
        origin.push(refspec=f"refs/heads/{branch}:refs/heads/{branch}")
        
        return {
            "success": True,
            "pushed_commits": commits_ahead,
            "branch": branch,
        }

    def pull_changes(
        self,
        repo_path: str,
        remote: str = "origin",
        branch: str | None = None,
    ) -> dict[str, Any]:
        """Pull changes from remote.
        
        Args:
            repo_path: Path to repository
            remote: Remote name
            branch: Branch to pull (default: current)
            
        Returns:
            Pull result dict
        """
        repo = self.open_repository(repo_path)
        
        if branch is None:
            branch = repo.active_branch.name
        
        origin = repo.remote(remote)
        
        # Pull
        origin.pull(f"refs/heads/{branch}:refs/heads/{branch}")
        
        # Get stats
        stats = repo.head.commit.stats
        
        return {
            "success": True,
            "files_changed": stats["files_changed"],
            "insertions": stats["insertions"],
            "deletions": stats["deletions"],
        }

    # ==================== GitHub API Operations ====================

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Make request to GitHub API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request parameters
            
        Returns:
            Response data
        """
        url = f"{self.GITHUB_API_URL}/{endpoint.lstrip('/')}"
        
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    def get_pull_requests(
        self,
        repo_url: str,
        state: str = "open",
    ) -> list[PullRequestInfo]:
        """Get pull requests.
        
        Args:
            repo_url: Repository URL
            state: PR state (open, closed, all)
            
        Returns:
            List of PullRequestInfo objects
        """
        owner, repo = self._parse_repo_url(repo_url)
        
        data = self._make_request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state},
        )
        
        return [
            PullRequestInfo(
                number=pr["number"],
                title=pr["title"],
                body=pr["body"],
                state=pr["state"],
                draft=pr["draft"],
                user=pr["user"]["login"],
                head_branch=pr["head"]["ref"],
                base_branch=pr["base"]["ref"],
                html_url=pr["html_url"],
                created_at=pr["created_at"],
                updated_at=pr["updated_at"],
            )
            for pr in data
        ]

    def create_pull_request(
        self,
        repo_path: str,
        request: PullRequestCreateRequest,
    ) -> PullRequestInfo:
        """Create a pull request.
        
        Args:
            repo_path: Path to repository
            request: PR creation request
            
        Returns:
            Created PullRequestInfo
        """
        repo = self.open_repository(repo_path)
        
        # Get remote URL
        if not repo.remotes:
            raise ValueError("No remote configured")
        
        remote_url = repo.remotes.origin.url
        owner, repo_name = self._parse_repo_url(remote_url)
        
        data = self._make_request(
            "POST",
            f"/repos/{owner}/{repo_name}/pulls",
            json={
                "title": request.title,
                "body": request.body or "",
                "head": request.head_branch,
                "base": request.base_branch,
                "draft": request.draft,
            },
        )
        
        return PullRequestInfo(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            draft=data["draft"],
            user=data["user"]["login"],
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
            html_url=data["html_url"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def get_issues(
        self,
        repo_url: str,
        state: str = "open",
        labels: list[str] | None = None,
    ) -> list[IssueInfo]:
        """Get issues.
        
        Args:
            repo_url: Repository URL
            state: Issue state (open, closed, all)
            labels: Filter by labels
            
        Returns:
            List of IssueInfo objects
        """
        owner, repo = self._parse_repo_url(repo_url)
        
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)
        
        data = self._make_request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params=params,
        )
        
        return [
            IssueInfo(
                number=issue["number"],
                title=issue["title"],
                body=issue["body"],
                state=issue["state"],
                user=issue["user"]["login"],
                labels=[l["name"] for l in issue["labels"]],
                assignees=[a["login"] for a in issue["assignees"]],
                comments=issue["comments"],
                created_at=issue["created_at"],
                updated_at=issue["updated_at"],
                closed_at=issue.get("closed_at"),
                html_url=issue["html_url"],
            )
            for issue in data
            if "pull_request" not in issue  # Filter out PRs
        ]

    def create_issue(
        self,
        repo_url: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> IssueInfo:
        """Create an issue.
        
        Args:
            repo_url: Repository URL
            title: Issue title
            body: Issue body
            labels: Issue labels
            assignees: Issue assignees
            
        Returns:
            Created IssueInfo
        """
        owner, repo = self._parse_repo_url(repo_url)
        
        data = self._make_request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json={
                "title": title,
                "body": body or "",
                "labels": labels or [],
                "assignees": assignees or [],
            },
        )
        
        return IssueInfo(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            user=data["user"]["login"],
            labels=[l["name"] for l in data["labels"]],
            assignees=[a["login"] for a in data["assignees"]],
            comments=data["comments"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            html_url=data["html_url"],
        )

    def update_issue(
        self,
        repo_url: str,
        issue_number: int,
        request: IssueUpdateRequest,
    ) -> IssueInfo:
        """Update an issue.
        
        Args:
            repo_url: Repository URL
            issue_number: Issue number
            request: Update request
            
        Returns:
            Updated IssueInfo
        """
        owner, repo = self._parse_repo_url(repo_url)
        
        json_data = {}
        if request.title is not None:
            json_data["title"] = request.title
        if request.body is not None:
            json_data["body"] = request.body
        if request.state is not None:
            json_data["state"] = request.state
        if request.labels is not None:
            json_data["labels"] = request.labels
        if request.assignees is not None:
            json_data["assignees"] = request.assignees
        
        data = self._make_request(
            "PATCH",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            json=json_data,
        )
        
        return IssueInfo(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            user=data["user"]["login"],
            labels=[l["name"] for l in data["labels"]],
            assignees=[a["login"] for a in data["assignees"]],
            comments=data["comments"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            closed_at=data.get("closed_at"),
            html_url=data["html_url"],
        )

    # ==================== Tree Operations ====================

    def get_tree(
        self,
        repo_path: str,
        path: str = "/",
        recursive: bool = False,
    ) -> list[TreeItem]:
        """Get repository tree.
        
        Args:
            repo_path: Path to repository
            path: Path within repository
            recursive: Include subdirectories
            
        Returns:
            List of TreeItem objects
        """
        repo = self.open_repository(repo_path)
        
        items = []
        repo_path_obj = Path(repo.working_dir)
        
        if path == "/":
            search_path = repo_path_obj
        else:
            search_path = repo_path_obj / path
        
        if not search_path.exists():
            return []
        
        for item in search_path.rglob("*") if recursive else search_path.iterdir():
            # Skip .git directory
            if ".git" in item.parts:
                continue
            
            rel_path = item.relative_to(repo_path_obj)
            
            if item.is_file():
                items.append(TreeItem(
                    path=str(rel_path),
                    type="blob",
                    size=item.stat().st_size,
                    sha="",
                ))
            elif item.is_dir():
                items.append(TreeItem(
                    path=str(rel_path) + "/",
                    type="tree",
                    size=None,
                    sha="",
                ))
        
        return items

    # ==================== File Operations ====================

    def read_file(
        self,
        repo_path: str,
        file_path: str,
        ref: str | None = None,
    ) -> FileContentResponse:
        """Read file content.
        
        Args:
            repo_path: Path to repository
            file_path: Path to file within repository
            ref: Branch or commit SHA
            
        Returns:
            FileContentResponse
        """
        repo = self.open_repository(repo_path)
        
        if ref:
            # Read from specific ref
            commit = repo.commit(ref)
            tree = commit.tree
            for path_part in file_path.strip("/").split("/"):
                tree = tree[path_part]
            
            content = tree.data_stream.read()
            sha = tree.hexsha
        else:
            # Read from working directory
            full_path = Path(repo.working_dir) / file_path
            if not full_path.exists():
                raise ValueError(f"File not found: {file_path}")
            
            content = full_path.read_bytes()
            sha = ""
        
        # Encode as base64 for binary safety
        encoded = base64.b64encode(content).decode()
        
        return FileContentResponse(
            path=file_path,
            content=encoded,
            encoding="base64",
            size=len(content),
            sha=sha,
            type="file",
        )

    def write_file(
        self,
        repo_path: str,
        file_path: str,
        content: str,
        message: str,
        branch: str | None = None,
    ) -> dict[str, Any]:
        """Write file to repository.
        
        Args:
            repo_path: Path to repository
            file_path: Path to file
            content: File content
            message: Commit message
            branch: Branch to commit to
            
        Returns:
            Write result
        """
        repo = self.open_repository(repo_path)
        
        # Write file
        full_path = Path(repo.working_dir) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        
        # Commit
        if branch:
            # Create branch if needed
            if branch not in [b.name for b in repo.branches]:
                repo.create_head(branch)
            repo.git.checkout(branch)
        
        self.commit_changes(repo_path, message, [file_path])
        
        return {
            "path": file_path,
            "sha": repo.head.commit.hexsha,
        }

    # ==================== Search Operations ====================

    def search(
        self,
        repo_path: str,
        request: SearchRequest,
    ) -> SearchResponse:
        """Search repository.
        
        Args:
            repo_path: Path to repository
            request: Search request
            
        Returns:
            SearchResponse
        """
        repo = self.open_repository(repo_path)
        
        # Get remote URL for API search
        if not repo.remotes:
            raise ValueError("No remote configured for search")
        
        remote_url = repo.remotes.origin.url
        owner, repo_name = self._parse_repo_url(remote_url)
        
        if request.search_type == "code":
            params = {
                "q": f"{request.query} repo:{owner}/{repo_name}",
            }
            if request.path:
                params["q"] += f" path:{request.path}"
            
            data = self._make_request("GET", "/search/code", params=params)
            
            results = [
                SearchResultItem(
                    type="code",
                    path=item["path"],
                    name=item["name"],
                    sha=item["sha"],
                    url=item["url"],
                    score=item["score"],
                )
                for item in data.get("items", [])
            ]
        
        elif request.search_type == "issues":
            params = {
                "q": f"{request.query} repo:{owner}/{repo_name}",
                "state": "open",
            }
            
            data = self._make_request("GET", "/search/issues", params=params)
            
            results = [
                SearchResultItem(
                    type="issue",
                    path=None,
                    name=item["title"],
                    sha=str(item["number"]),
                    url=item["html_url"],
                    score=item["score"],
                )
                for item in data.get("items", [])
            ]
        
        elif request.search_type == "commits":
            params = {
                "q": f"{request.query} repo:{owner}/{repo_name}",
            }
            
            data = self._make_request("GET", "/search/commits", params=params)
            
            results = [
                SearchResultItem(
                    type="commit",
                    path=None,
                    name=item["commit"]["message"].split("\n")[0],
                    sha=item["sha"],
                    url=item["html_url"],
                    score=1.0,
                )
                for item in data.get("items", [])
            ]
        
        else:
            raise ValueError(f"Unknown search type: {request.search_type}")
        
        return SearchResponse(
            total=data.get("total_count", 0),
            results=results,
        )
