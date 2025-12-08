# Azure DevOps MCP Server

A Model Context Protocol (MCP) server that provides AI-powered tools for interacting with Azure DevOps repositories and pull requests. Built with FastMCP for seamless integration with Claude and other MCP-compatible AI assistants.

## 🚀 Features

- **Repository Management** - Resolve repository IDs from names or GUIDs
- **Pull Request Operations** - List, inspect, and comment on PRs
- **Diff Analysis** - Fetch complete unified diffs with original and modified content
- **Code Review** - Built-in review policy and automated review capabilities
- **Comment Threading** - Add inline or top-level PR comments
- **Auto-Discovery** - Automatic tool and resource registration
- **Extensible Architecture** - Simple pattern for adding new functionality

## 📁 Project Structure

```
AzureDevopsMcp/
├── src/
│   ├── config.py              # Global MCP instance & configuration
│   ├── client.py              # HTTP client for Azure DevOps API
│   ├── server.py              # Server entry point
│   ├── utils/
│   │   └── helpers.py         # Helper functions (repo resolution, blob fetching)
│   ├── tools/
│   │   ├── __init__.py        # Auto-import tool modules
│   │   ├── repository.py      # Repository tools
│   │   └── pull_requests.py   # Pull request tools
│   └── policies/
│       ├── __init__.py        # Auto-import policy modules
│       └── review_policy.py   # Code review policy resource
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
└── README.md

## ⚙️ Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd AzureDevopsMcp
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
ADO_ORG_URL=https://dev.azure.com/YourOrganization
ADO_PROJECT=YourProjectName
ADO_PAT=your_personal_access_token_here
```

**Getting a Personal Access Token (PAT):**
1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create new token with permissions: `Code (Read)` and `Pull Request Threads (Read & Write)`
3. Copy the token to your `.env` file

### 3. Run the Server

```bash
python main.py
```

The server will run in stdio mode, ready to accept MCP protocol requests.

## 🛠️ Available Tools

### Repository Tools

#### `resolve_repo_id(repo_key: str) -> str`
Converts a repository name to its GUID identifier.

**Parameters:**
- `repo_key` - Repository name (e.g., "my-api") or GUID

**Returns:** Repository GUID

**Example:**
```python
repo_id = resolve_repo_id("road-api")
# Returns: "7c9a1f2e-1234-4d5e-9abc-0f1122334455"
```

---

### Pull Request Tools

#### `list_pull_requests(repo_id: str, status: str = "active", top: int = 10) -> List[Dict]`
Lists pull requests for a repository with filtering options.

**Parameters:**
- `repo_id` - Repository GUID from `resolve_repo_id`
- `status` - Filter by status: `"active"`, `"completed"`, `"abandoned"`
- `top` - Maximum number of PRs to return

**Returns:** List of PR metadata dictionaries

---

#### `get_pull_request(repo_id: str, pr_id: int) -> str`
Retrieves detailed information about a specific pull request.

**Returns:** Formatted string with PR details (title, author, branches, description)

---

#### `get_pull_request_full_diff(repo_id: str, pr_id: int) -> Dict[str, Any]`
Fetches complete diff and all review comments for a PR.

**Returns:**
```python
{
    "diff": "unified diff with original/modified content",
    "comments": [
        {
            "file": "path/to/file.py",
            "line": 42,
            "content": "comment text",
            "author": "Jane Doe",
            "status": "active",
            "threadId": 123,
            "commentId": 456
        }
    ]
}
```

**Note:** Should be used with `get_review_policy()` resource for automated reviews.

---

#### `add_pull_request_comment(repo_id: str, pr_id: int, comment: str, file_path: str = None, line: int = None) -> str`
Adds a comment to a pull request.

**Parameters:**
- `file_path` & `line` - Optional. If provided, creates inline comment at specific location
- If omitted, creates top-level PR comment

**Returns:** Confirmation message with thread ID

---

## 📚 Resources

### `policy://review` - Code Review Policy
Official code review standards and expectations for PR reviews. This resource defines:
- Schema & model design standards
- Validation requirements
- API layer expectations
- Service layer principles
- Documentation standards
- Testing requirements
- Review style guidelines

**Usage:** LLMs should load this resource before performing automated code reviews.

## 🔧 Extending the Server

The server uses a simple, extensible architecture. Adding new tools or resources requires just two steps:

### Adding a New Tool

**Step 1:** Create your tool module

```python
# src/tools/workitems.py
from ..config import mcp
from ..client import client
from ..config import ADO_ORG_URL, ADO_PROJECT

@mcp.tool()
def get_workitem(workitem_id: int) -> dict:
    """
    Retrieve a work item by ID.

    Parameters:
    - workitem_id: The numeric ID of the work item

    Returns:
    - Dictionary with work item details
    """
    url = f"{ADO_ORG_URL}/{ADO_PROJECT}/_apis/wit/workitems/{workitem_id}?api-version=7.1"
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()

@mcp.tool()
def list_workitems(query: str) -> list:
    """List work items matching a WIQL query."""
    # Implementation here
    pass
```

**Step 2:** Register the module in `src/tools/__init__.py`

```python
"""Auto-import all tool modules to register them."""
from . import repository  # noqa: F401
from . import pull_requests  # noqa: F401
from . import workitems  # noqa: F401  ← Add this line
```

Done! Your tools are now available via the MCP protocol.

---

### Adding a New Resource

**Step 1:** Create your resource module

```python
# src/policies/testing_policy.py
from ..config import mcp

TESTING_POLICY = """
Testing Standards
=================
1. All features must have unit tests
2. Integration tests for API endpoints
3. Minimum 80% code coverage
"""

@mcp.resource(
    uri="policy://testing",
    name="Testing Policy",
    description="Official testing standards and requirements"
)
def get_testing_policy() -> str:
    """Returns the testing policy documentation."""
    return TESTING_POLICY
```

**Step 2:** Register in `src/policies/__init__.py`

```python
"""Auto-import all policy/resource modules to register them."""
from . import review_policy  # noqa: F401
from . import testing_policy  # noqa: F401  ← Add this line
```

---

## 🏗️ Architecture

The server follows a clean, modular architecture:

- **Global MCP Instance** (`src/config.py`) - Single FastMCP instance shared across all modules
- **Auto-Discovery** - Modules self-register by importing in `__init__.py`
- **Separation of Concerns** - Tools, resources, utilities, and configuration cleanly separated
- **Type Safety** - Full type hints for better IDE support and error checking



## 🤝 Contributing

Contributions welcome! Please follow the existing code structure and patterns when adding new functionality.
