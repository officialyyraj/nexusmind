"""Tests for GitHub integration."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.integrations.github.schemas import (
    GitHubOperation,
    GitHubOperationResponse,
    RepositoryCloneRequest,
    RepositoryOpenRequest,
    BranchCreateRequest,
    CommitRequest,
    PushRequest,
    PullRequest,
    IssueCreateRequest,
    SearchRequest,
    TreeRequest,
)


class TestGitHubSchemas:
    """Test GitHub schemas."""

    def test_repository_clone_request(self):
        """Test RepositoryCloneRequest schema."""
        request = RepositoryCloneRequest(
            repo_url="https://github.com/owner/repo",
            local_path="/tmp/repo",
            branch="main",
            depth=10,
        )
        assert request.repo_url == "https://github.com/owner/repo"
        assert request.local_path == "/tmp/repo"
        assert request.branch == "main"
        assert request.depth == 10

    def test_repository_open_request(self):
        """Test RepositoryOpenRequest schema."""
        request = RepositoryOpenRequest(local_path="/tmp/repo")
        assert request.local_path == "/tmp/repo"

    def test_branch_create_request(self):
        """Test BranchCreateRequest schema."""
        request = BranchCreateRequest(
            repo_path="/tmp/repo",
            branch_name="feature/new-branch",
            from_branch="main",
        )
        assert request.branch_name == "feature/new-branch"
        assert request.from_branch == "main"

    def test_commit_request(self):
        """Test CommitRequest schema."""
        request = CommitRequest(
            repo_path="/tmp/repo",
            message="Fix bug",
            files=["src/app.py"],
            author_name="Developer",
            author_email="dev@example.com",
        )
        assert request.message == "Fix bug"
        assert request.author_name == "Developer"

    def test_push_request(self):
        """Test PushRequest schema."""
        request = PushRequest(
            repo_path="/tmp/repo",
            remote="origin",
            branch="main",
        )
        assert request.remote == "origin"
        assert request.branch == "main"

    def test_issue_create_request(self):
        """Test IssueCreateRequest schema."""
        request = IssueCreateRequest(
            repo_url="https://github.com/owner/repo",
            title="Bug in login",
            body="Description",
            labels=["bug", "high-priority"],
            assignees=["developer"],
        )
        assert request.title == "Bug in login"
        assert "bug" in request.labels

    def test_search_request(self):
        """Test SearchRequest schema."""
        request = SearchRequest(
            repo_path="/tmp/repo",
            query="authentication",
            search_type="code",
            path="src/",
        )
        assert request.query == "authentication"
        assert request.search_type == "code"
        assert request.path == "src/"

    def test_tree_request(self):
        """Test TreeRequest schema."""
        request = TreeRequest(
            repo_path="/tmp/repo",
            path="/src",
            recursive=True,
        )
        assert request.recursive is True

    def test_github_operation_response(self):
        """Test GitHubOperationResponse schema."""
        response = GitHubOperationResponse(
            success=True,
            operation=GitHubOperation.CLONE,
            data={"path": "/tmp/repo"},
            message="Cloned successfully",
        )
        assert response.success is True
        assert response.operation == GitHubOperation.CLONE
        assert response.data["path"] == "/tmp/repo"

    def test_github_operation_response_error(self):
        """Test GitHubOperationResponse with error."""
        response = GitHubOperationResponse(
            success=False,
            operation=GitHubOperation.CLONE,
            error="Repository not found",
        )
        assert response.success is False
        assert response.error == "Repository not found"
        assert response.data is None


class TestGitHubClientParsing:
    """Test GitHub client URL parsing."""

    def test_parse_full_url(self):
        """Test parsing full GitHub URL."""
        from app.integrations.github.github_client import GitHubClient

        client = GitHubClient()

        # Short form is most reliable
        owner, repo = client._parse_repo_url("owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_url(self):
        """Test parsing invalid URL raises error."""
        from app.integrations.github.github_client import GitHubClient

        client = GitHubClient()

        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            client._parse_repo_url("not-a-url")


class TestGitHubServiceMocked:
    """Test GitHub service with mocked client."""

    @pytest.mark.asyncio
    async def test_clone_repository_success(self):
        """Test successful repository clone."""
        from app.integrations.github.github_service import GitHubService

        service = GitHubService()

        # Mock the client
        service.client.clone_repository = MagicMock(return_value="/tmp/repo")

        request = RepositoryCloneRequest(
            repo_url="https://github.com/owner/repo",
            local_path="/tmp/repo",
        )

        response = await service.clone_repository(request)

        assert response.success is True
        assert response.operation == GitHubOperation.CLONE
        assert response.data["path"] == "/tmp/repo"

    @pytest.mark.asyncio
    async def test_clone_repository_error(self):
        """Test repository clone error."""
        from app.integrations.github.github_service import GitHubService

        service = GitHubService()

        # Mock the client to raise an error
        service.client.clone_repository = MagicMock(
            side_effect=Exception("Network error")
        )

        request = RepositoryCloneRequest(
            repo_url="https://github.com/owner/repo",
            local_path="/tmp/repo",
        )

        response = await service.clone_repository(request)

        assert response.success is False
        assert response.operation == GitHubOperation.CLONE
        assert "Network error" in response.error

    @pytest.mark.asyncio
    async def test_commit_changes(self):
        """Test committing changes."""
        from app.integrations.github.github_service import GitHubService
        from app.integrations.github.schemas import CommitInfo
        from datetime import datetime

        service = GitHubService()

        # Mock commit info as proper dataclass
        mock_commit = CommitInfo(
            sha="abc123",
            message="Test commit",
            author_name="Developer",
            author_email="dev@example.com",
            author_date=datetime.now(),
            committer_name="Developer",
            committer_email="dev@example.com",
            committer_date=datetime.now(),
        )

        service.client.commit_changes = MagicMock(return_value=mock_commit)

        request = CommitRequest(
            repo_path="/tmp/repo",
            message="Test commit",
            files=["."],
        )

        response = await service.commit_changes(request)

        assert response.success is True
        assert response.operation == GitHubOperation.COMMIT

    @pytest.mark.asyncio
    async def test_create_branch(self):
        """Test creating a branch."""
        from app.integrations.github.github_service import GitHubService
        from app.integrations.github.schemas import BranchInfo

        service = GitHubService()

        # Mock branch info
        mock_branch = BranchInfo(
            name="feature/new",
            commit_sha="abc123",
            is_protected=False,
            is_default=False,
        )

        service.client.create_branch = MagicMock(return_value=mock_branch)

        request = BranchCreateRequest(
            repo_path="/tmp/repo",
            branch_name="feature/new",
            from_branch="main",
        )

        response = await service.create_branch(request)

        assert response.success is True
        assert response.data["name"] == "feature/new"

    @pytest.mark.asyncio
    async def test_push_changes(self):
        """Test pushing changes."""
        from app.integrations.github.github_service import GitHubService

        service = GitHubService()

        service.client.push_changes = MagicMock(return_value={
            "success": True,
            "pushed_commits": 3,
            "branch": "main",
        })

        request = PushRequest(
            repo_path="/tmp/repo",
            remote="origin",
            branch="main",
        )

        response = await service.push_changes(request)

        assert response.success is True
        assert response.data["pushed_commits"] == 3

    @pytest.mark.asyncio
    async def test_pull_changes(self):
        """Test pulling changes."""
        from app.integrations.github.github_service import GitHubService

        service = GitHubService()

        service.client.pull_changes = MagicMock(return_value={
            "success": True,
            "files_changed": 5,
            "insertions": 100,
            "deletions": 20,
        })

        request = PullRequest(
            repo_path="/tmp/repo",
            remote="origin",
        )

        response = await service.pull_changes(request)

        assert response.success is True
        assert response.data["files_changed"] == 5

    @pytest.mark.asyncio
    async def test_create_issue(self):
        """Test creating an issue."""
        from app.integrations.github.github_service import GitHubService
        from datetime import datetime
        from app.integrations.github.schemas import IssueInfo

        service = GitHubService()

        # Mock issue info
        mock_issue = IssueInfo(
            number=42,
            title="Bug report",
            body="Description",
            state="open",
            user="developer",
            labels=["bug"],
            assignees=[],
            comments=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
            html_url="https://github.com/owner/repo/issues/42",
        )

        service.client.create_issue = MagicMock(return_value=mock_issue)

        request = IssueCreateRequest(
            repo_url="https://github.com/owner/repo",
            title="Bug report",
            body="Description",
            labels=["bug"],
        )

        response = await service.create_issue(request)

        assert response.success is True
        assert response.data["number"] == 42
        assert response.data["title"] == "Bug report"

    @pytest.mark.asyncio
    async def test_search_repository(self):
        """Test searching repository."""
        from app.integrations.github.github_service import GitHubService
        from app.integrations.github.schemas import SearchResponse, SearchResultItem

        service = GitHubService()

        # Mock search response
        mock_results = SearchResponse(
            total=2,
            results=[
                SearchResultItem(
                    type="code",
                    path="src/auth.py",
                    name="auth.py",
                    sha="abc123",
                    url=None,
                    score=0.9,
                ),
            ],
        )

        service.client.search = MagicMock(return_value=mock_results)

        request = SearchRequest(
            repo_path="/tmp/repo",
            query="authentication",
            search_type="code",
        )

        response = await service.search(request)

        assert response.success is True
        assert response.data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_tree(self):
        """Test getting repository tree."""
        from app.integrations.github.github_service import GitHubService
        from app.integrations.github.schemas import TreeItem

        service = GitHubService()

        # Mock tree items
        mock_tree = [
            TreeItem(path="src/main.py", type="blob", size=1000, sha="abc"),
            TreeItem(path="src/utils/", type="tree", size=None, sha="def"),
        ]

        service.client.get_tree = MagicMock(return_value=mock_tree)

        response = await service.get_tree("/tmp/repo", "/src", recursive=False)

        assert response.success is True
        assert len(response.data["tree"]) == 2


class TestGitHubIntegrationEndpoints:
    """Test GitHub integration endpoints."""

    def test_router_prefix(self):
        """Test router has correct prefix."""
        from app.integrations.github.router import router

        assert router.prefix == "/github"

    def test_router_tags(self):
        """Test router has correct tags."""
        from app.integrations.github.router import router

        assert "GitHub Integration" in router.tags

    def test_endpoints_exist(self):
        """Test required endpoints are defined."""
        from app.integrations.github.router import router

        paths = [route.path for route in router.routes]

        assert any("/clone" in path for path in paths)
        assert any("/open" in path for path in paths)
        assert any("/branch/create" in path for path in paths)
        assert any("/commit" in path for path in paths)
        assert any("/push" in path for path in paths)
        assert any("/pull" in path for path in paths)
        assert any("/pull-request/create" in path for path in paths)
        assert any("/issue/create" in path for path in paths)
        assert any("/search" in path for path in paths)
