# Azure DevOps MCP Server

A Model Context Protocol (MCP) server that provides AI-powered tools for interacting with Azure DevOps repositories, pull requests, and work items. Built with FastMCP for seamless integration with Claude and other MCP-compatible AI assistants.

## Features

- **Project Discovery** - List all accessible Azure DevOps projects
- **Repository Management** - Resolve repository IDs, list branches
- **Pull Request Operations** - List, create, inspect, and comment on PRs
- **Work Item Management** - Create PBIs, Bugs, and custom work items
- **Diff Analysis** - Fetch complete unified diffs with original and modified content
- **Code Review** - Built-in review policy and automated review capabilities
- **PR-Work Item Linking** - Link pull requests to work items
- **Auto-Discovery** - Automatic tool and resource registration
- **Extensible Architecture** - Simple pattern for adding new functionality

## Project Structure

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
│   │   ├── repository.py      # Repository & project tools
│   │   ├── pull_requests.py   # Pull request tools
│   │   └── work_items.py      # Work item tools (PBI, Bug, etc.)
│   └── policies/
│       ├── __init__.py        # Auto-import policy modules
│       └── review_policy.py   # Code review policy resource
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
└── README.md
```

## Setup

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
ADO_PROJECT=YourDefaultProject
ADO_PAT=your_personal_access_token_here
```

**Getting a Personal Access Token (PAT):**
1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create new token with permissions:
   - `Code (Read & Write)` - for repository and PR operations
   - `Pull Request Threads (Read & Write)` - for PR comments
   - `Work Items (Read & Write)` - for creating/updating work items
3. Copy the token to your `.env` file

### 3. Run the Server

```bash
python main.py
```

The server will run in stdio mode, ready to accept MCP protocol requests.

## Available Tools

### Project & Repository Tools

#### `list_projects() -> List[Dict]`
Lists all Azure DevOps projects you have access to.

**Returns:** List of projects with name, id, description, and state.

**Usage:** Call this before creating work items to discover available projects.

---

#### `resolve_repo_id(repo_key: str, project: str = None) -> str`
Converts a repository name to its GUID identifier.

**Parameters:**
- `repo_key` - Repository name (e.g., "my-api") or GUID

**Returns:** Repository GUID

---

#### `list_branches(repo_id: str, filter_name: str = None, top: int = 100) -> List[Dict]`
Lists branches in a repository.

**Parameters:**
- `repo_id` - Repository GUID from `resolve_repo_id`
- `filter_name` - Optional filter by name prefix (e.g., "feature/")
- `top` - Maximum number of branches to return

**Returns:** List of branches with name, fullName, isDefault, creator, objectId

---

### Pull Request Tools

#### `list_pull_requests(repo_id: str, status: str = "active", top: int = 10) -> List[Dict]`
Lists pull requests for a repository.

**Parameters:**
- `repo_id` - Repository GUID
- `status` - Filter: `"active"`, `"completed"`, `"abandoned"`
- `top` - Maximum number of PRs

---

#### `get_pull_request(repo_id: str, pr_id: int) -> str`
Retrieves detailed information about a specific pull request.

---

#### `create_pull_request(repo_id: str, source_branch: str, target_branch: str, title: str, description: str = None, work_item_ids: List[int] = None) -> Dict`
Creates a new pull request.

**Parameters:**
- `repo_id` - Repository GUID
- `source_branch` - Full ref name (e.g., "refs/heads/feature/my-feature")
- `target_branch` - Full ref name (e.g., "refs/heads/main")
- `title` - PR title
- `description` - Optional PR description
- `work_item_ids` - Optional list of work item IDs to link

**Returns:** Created PR details including id, url, title, status

---

#### `set_pr_description(repo_id: str, pr_id: int, description: str) -> Dict`
Updates the description of an existing pull request.

**LLM Instructions:** The description should include a structured format with:
- Summary section with bullet points
- Test plan section with checkboxes
- Auto-detected checkboxes for tests and documentation based on diff analysis

---

#### `get_pull_request_full_diff(repo_id: str, pr_id: int) -> Dict`
Fetches complete diff and all review comments for a PR.

---

#### `add_pull_request_comment(repo_id: str, pr_id: int, comment: str, file_path: str = None, line: int = None) -> str`
Adds a comment to a pull request (top-level or inline).

---

#### `link_pr_to_work_item(repo_id: str, pr_id: int, work_item_id: int, project: str) -> Dict`
Links a pull request to a work item.

---

### Work Item Tools

#### `list_work_item_types(project: str) -> List[Dict]`
Lists all available work item types in a project.

**Usage:** Call this to discover what work item types are available (Bug, PBI, Task, etc.).

---

#### `list_area_paths(project: str, depth: int = 3) -> List[Dict]`
Lists all area paths in a project for organizing work items.

---

#### `list_iteration_paths(project: str, depth: int = 3) -> List[Dict]`
Lists all iteration paths (sprints) in a project.

---

#### `create_product_backlog_item(project: str, title: str, assigned_to: str, ...) -> Dict`
Creates a new Product Backlog Item (PBI).

**Required Parameters:**
- `project` - Project name (use `list_projects()` first)
- `title` - PBI title
- `assigned_to` - Email or display name of assignee

**Optional Parameters:**
- `description` - HTML description
- `acceptance_criteria` - HTML acceptance criteria
- `area_path` - Area path for organization
- `iteration_path` - Sprint assignment
- `priority` - Priority (1-4)
- `tags` - Semicolon-separated tags

---

#### `create_bug(project: str, title: str, assigned_to: str, description: str, steps_to_reproduce: str, expected_behavior: str, ...) -> Dict`
Creates a new Bug work item (using custom "Bugs" type with required fields).

**Required Parameters:**
- `project` - Project name
- `title` - Bug title
- `assigned_to` - Assignee
- `description` - Bug description
- `steps_to_reproduce` - Steps to reproduce the bug
- `expected_behavior` - Expected app behavior

**Optional Parameters:**
- `environment` - Environment (default: "Dev")
- `area_path`, `iteration_path`, `priority`, `tags`

---

#### `create_work_item(project: str, work_item_type: str, title: str, assigned_to: str, ...) -> Dict`
Creates a work item of ANY type. Most flexible tool for custom work item types.

**Parameters:**
- `work_item_type` - Exact type name from `list_work_item_types()`
- `custom_fields` - Dict of custom field reference names to values

**Example with custom fields:**
```python
create_work_item(
    project="MyProject",
    work_item_type="Bugs",
    title="Fix login error",
    assigned_to="john@company.com",
    custom_fields={
        "Custom.Environment": "Dev",
        "Custom.Stepstoreproduce": "1. Go to login\n2. Click submit",
        "Custom.Expectedappbehavior": "User should be logged in"
    }
)
```

---

## Resources

### `policy://review` - Code Review Policy
Official code review standards and expectations for PR reviews.

**Usage:** LLMs should load this resource before performing automated code reviews.

## Extending the Server

### Adding a New Tool

**Step 1:** Create your tool module in `src/tools/`

```python
# src/tools/my_tools.py
from ..config import mcp, ADO_ORG_URL
from ..client import client

@mcp.tool()
def my_new_tool(param: str) -> dict:
    """Tool description for LLM."""
    # Implementation
    pass
```

**Step 2:** Register in `src/tools/__init__.py`

```python
from . import my_tools  # noqa: F401
```

### Adding a New Resource

**Step 1:** Create resource module in `src/policies/`

```python
# src/policies/my_policy.py
from ..config import mcp

@mcp.resource(uri="policy://my-policy", name="My Policy", description="...")
def get_my_policy() -> str:
    return "Policy content..."
```

**Step 2:** Register in `src/policies/__init__.py`

## Architecture

- **Global MCP Instance** (`src/config.py`) - Single FastMCP instance shared across all modules
- **Auto-Discovery** - Modules self-register by importing in `__init__.py`
- **Separation of Concerns** - Tools, resources, utilities, and configuration cleanly separated
- **Type Safety** - Full type hints for better IDE support and error checking

## Contributing

Contributions welcome! Please follow the existing code structure and patterns when adding new functionality.
