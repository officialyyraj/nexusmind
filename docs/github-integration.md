# GitHub Integration

The GitHub integration provides comprehensive repository management capabilities using GitPython and the GitHub REST API.

## Architecture

```
app/integrations/github/
├── __init__.py          # Module exports
├── schemas.py            # Pydantic request/response models
├── github_client.py      # GitPython + GitHub API client
├── github_service.py     # Business logic layer
└── router.py            # FastAPI endpoints
```

## Features

### Repository Operations
- **Clone Repository** - Clone any GitHub repository
- **Open Repository** - Open existing local repository
- **Get Info** - Retrieve repository metadata

### Branch Operations
- **Create Branch** - Create new branches
- **List Branches** - List all branches

### Commit Operations
- **Commit Changes** - Stage and commit files
- **Push** - Push commits to remote
- **Pull** - Pull changes from remote

### Pull Request Operations
- **Get PRs** - List pull requests
- **Create PR** - Create new pull request

### Issue Operations
- **Get Issues** - List repository issues
- **Create Issue** - Create new issue
- **Update Issue** - Modify existing issue

### File Operations
- **Read Tree** - List repository structure
- **Read File** - Get file content
- **Write File** - Create/update files

### Search
- **Code Search** - Search code in repository
- **Issue Search** - Search issues
- **Commit Search** - Search commits

## API Endpoints

### Repository Endpoints
```
POST /api/v1/github/clone         # Clone repository
POST /api/v1/github/open          # Open repository
GET  /api/v1/github/repo/{path}/info  # Get info
```

### Branch Endpoints
```
POST /api/v1/github/branch/create      # Create branch
GET  /api/v1/github/repo/{path}/branches  # List branches
```

### Commit Endpoints
```
POST /api/v1/github/commit   # Commit changes
POST /api/v1/github/push    # Push changes
POST /api/v1/github/pull     # Pull changes
```

### Pull Request Endpoints
```
GET  /api/v1/github/repo/{url}/pulls          # List PRs
POST /api/v1/github/pull-request/create       # Create PR
```

### Issue Endpoints
```
GET  /api/v1/github/repo/{url}/issues        # List issues
POST /api/v1/github/issue/create             # Create issue
PATCH /api/v1/github/repo/{url}/issues/{id}  # Update issue
```

### File Endpoints
```
GET  /api/v1/github/repo/{path}/tree             # List tree
GET  /api/v1/github/repo/{path}/file/{file}     # Read file
```

### Search Endpoints
```
POST /api/v1/github/search  # Search repository
```

## Usage Examples

### Clone a Repository
```python
from app.integrations.github import GitHubService, RepositoryCloneRequest

service = GitHubService(token="ghp_xxx")
request = RepositoryCloneRequest(
    repo_url="https://github.com/owner/repo",
    local_path="/workspace/repo",
    branch="main"
)
response = await service.clone_repository(request)
```

### Create a Branch and Commit
```python
from app.integrations.github import (
    GitHubService, BranchCreateRequest, CommitRequest
)

# Create branch
branch_request = BranchCreateRequest(
    repo_path="/workspace/repo",
    branch_name="feature/new-feature",
    from_branch="main"
)
await service.create_branch(branch_request)

# Commit changes
commit_request = CommitRequest(
    repo_path="/workspace/repo",
    message="Add new feature",
    files=["src/feature.py"]
)
await service.commit_changes(commit_request)
```

### Create Pull Request
```python
from app.integrations.github import GitHubService, PullRequestCreateRequest

request = PullRequestCreateRequest(
    repo_path="/workspace/repo",
    title="Add new feature",
    body="This PR adds...",
    head_branch="feature/new-feature",
    base_branch="main"
)
response = await service.create_pull_request(request)
```

### Create Issue
```python
from app.integrations.github import GitHubService, IssueCreateRequest

request = IssueCreateRequest(
    repo_url="https://github.com/owner/repo",
    title="Bug: Login fails",
    body="Steps to reproduce...",
    labels=["bug", "high-priority"],
    assignees=["developer"]
)
response = await service.create_issue(request)
```

### Search Code
```python
from app.integrations.github import GitHubService, SearchRequest

request = SearchRequest(
    repo_path="/workspace/repo",
    query="authentication",
    search_type="code",
    path="src/"
)
response = await service.search(request)
```

## Authentication

### Using Personal Access Token
Set the `Authorization: Bearer <token>` header or initialize the service with a token:

```python
service = GitHubService(token="ghp_xxx")
```

### Permissions
The token requires these scopes:
- `repo` - Full repository access
- `read:user` - User information
- `notifications` - For notifications

## Response Format

All operations return a `GitHubOperationResponse`:

```python
@dataclass
class GitHubOperationResponse:
    success: bool           # Operation success
    operation: str          # Operation type
    data: dict | None     # Response data
    message: str | None    # Human message
    error: str | None     # Error message if failed
```

## Error Handling

```python
response = await service.clone_repository(request)
if not response.success:
    print(f"Error: {response.error}")
else:
    print(f"Success: {response.message}")
```

## Testing

```bash
pytest tests/integrations/github/test_github.py -v
```

All 24 tests pass covering:
- Schema validation
- URL parsing
- Service operations
- API endpoints
