"""Work item-related MCP tools."""
from typing import Dict, Any, Optional, List
from ..config import mcp, ADO_ORG_URL
from ..client import client


def _flatten_classification_nodes(node: Dict[str, Any], result: List[Dict[str, Any]]) -> None:
    """Recursively flatten a classification node tree into a list."""
    result.append({
        "path": node.get("path", ""),
        "name": node.get("name", ""),
        "id": node.get("id"),
    })
    for child in node.get("children", []):
        _flatten_classification_nodes(child, result)


@mcp.tool()
def list_work_item_types(project: str) -> List[Dict[str, Any]]:
    """
    List all available work item types in an Azure DevOps project.

    Use this tool to discover what work item types are available in the project
    (e.g., Bug, Product Backlog Item, Task, Feature, Epic, etc.).
    Different process templates (Scrum, Agile, Basic, CMMI) have different work item types.

    Parameters:
    -----------
    project : str
        REQUIRED. The project name. Use list_projects() to discover available projects.

    Returns:
    --------
    List[Dict[str, Any]]
        A list of work item types, each containing:
        - name: The work item type name (e.g., "Bug", "Product Backlog Item")
        - description: Description of the work item type
        - icon: Icon URL for the work item type

    Example Usage:
    --------------
    Call this to discover available work item types:
        "What work item types are available?"
        "Can I create bugs in this project?"
    """
    url = (
        f"{ADO_ORG_URL}/{project}/_apis/wit/workitemtypes"
        f"?api-version=7.1-preview.2"
    )

    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    types = data.get("value", [])

    result: List[Dict[str, Any]] = []
    for wit in types:
        result.append({
            "name": wit.get("name"),
            "description": wit.get("description"),
            "icon": wit.get("icon", {}).get("url"),
        })

    return result


@mcp.tool()
def list_area_paths(project: str, depth: int = 3) -> List[Dict[str, Any]]:
    """
    List all available area paths in an Azure DevOps project.

    Area paths are used to organize work items by team, feature area, or component.
    Call this tool BEFORE creating a PBI if you need to discover valid area paths.

    Parameters:
    -----------
    project : str
        REQUIRED. The project name. Use list_projects() to discover available projects.

    depth : int, optional
        How many levels deep to retrieve (default: 3).
        - depth=1: Only root area
        - depth=2: Root + immediate children
        - depth=3+: Deeper hierarchy

    Returns:
    --------
    List[Dict[str, Any]]
        A list of area paths, each containing:
        - path: Full path (e.g., "MyProject\\Team A\\Frontend") - use this in create_product_backlog_item
        - name: Just the node name (e.g., "Frontend")
        - id: The internal node ID

    Example Usage:
    --------------
    Call this when the user asks:
        "What areas can I create a PBI in?"
        "Show me the available area paths"
        "Where can I put this backlog item?"
    """
    url = (
        f"{ADO_ORG_URL}/{project}/_apis/wit/classificationnodes/Areas"
        f"?$depth={depth}&api-version=7.1-preview.2"
    )

    resp = client.get(url)
    resp.raise_for_status()

    root = resp.json()
    result: List[Dict[str, Any]] = []
    _flatten_classification_nodes(root, result)

    return result


@mcp.tool()
def list_iteration_paths(project: str, depth: int = 3) -> List[Dict[str, Any]]:
    """
    List all available iteration paths (sprints) in an Azure DevOps project.

    Iteration paths represent sprints or time-boxed periods for scheduling work.
    Call this tool BEFORE creating a PBI if you need to assign it to a specific sprint.

    Parameters:
    -----------
    project : str
        REQUIRED. The project name. Use list_projects() to discover available projects.

    depth : int, optional
        How many levels deep to retrieve (default: 3).

    Returns:
    --------
    List[Dict[str, Any]]
        A list of iteration paths, each containing:
        - path: Full path (e.g., "MyProject\\Sprint 1") - use this in create_product_backlog_item
        - name: Just the node name (e.g., "Sprint 1")
        - id: The internal node ID

    Example Usage:
    --------------
    Call this when the user asks:
        "What sprints are available?"
        "Show me the iterations"
        "Which sprint should I add this to?"
    """
    url = (
        f"{ADO_ORG_URL}/{project}/_apis/wit/classificationnodes/Iterations"
        f"?$depth={depth}&api-version=7.1-preview.2"
    )

    resp = client.get(url)
    resp.raise_for_status()

    root = resp.json()
    result: List[Dict[str, Any]] = []
    _flatten_classification_nodes(root, result)

    return result


@mcp.tool()
def create_product_backlog_item(
    project: str,
    title: str,
    assigned_to: str,
    description: Optional[str] = None,
    acceptance_criteria: Optional[str] = None,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    priority: Optional[int] = None,
    tags: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new Product Backlog Item (PBI) in Azure DevOps.

    IMPORTANT: Before calling this tool, the LLM MUST:
    1. Call list_projects() to get available projects
    2. Ask the user to choose a project if not specified

    Parameters:
    -----------
    project : str
        REQUIRED. The project name where the PBI will be created.
        Use list_projects() to discover available projects.

    title : str
        REQUIRED. The title of the PBI. Should be a concise summary of the backlog item.

    assigned_to : str
        REQUIRED. The email address or display name of the person to assign the PBI to.
        Every PBI must have an owner.

    description : str, optional
        The detailed description of the PBI. Supports HTML formatting.
        This field typically describes WHAT the PBI is about and WHY it's needed.

    acceptance_criteria : str, optional
        The acceptance criteria that define when this PBI is considered complete.
        Supports HTML formatting. Use clear, testable criteria like:
        - "User can log in with email and password"
        - "Error message displays when credentials are invalid"

    area_path : str, optional
        The area path for organizing the PBI (e.g., "MyProject\\Team A\\Frontend").
        Use list_area_paths(project) to discover available paths.

    iteration_path : str, optional
        The iteration/sprint path (e.g., "MyProject\\Sprint 1").
        Use list_iteration_paths(project) to discover available paths.

    priority : int, optional
        The priority of the PBI (typically 1-4, where 1 is highest priority).

    tags : str, optional
        Semicolon-separated tags to apply to the PBI (e.g., "frontend;urgent;tech-debt").

    Returns:
    --------
    Dict[str, Any]
        A dictionary containing the created PBI details:
        - id: The work item ID
        - url: Direct URL to the work item
        - title: The title
        - state: The initial state (usually "New")
        - assignedTo: The person assigned
        - areaPath: The area path
        - iterationPath: The iteration path

    Example Usage:
    --------------
    The LLM should:
    1. Call list_projects() first
    2. Ask user to choose a project
    3. Then call create_product_backlog_item with the chosen project

    Example call:
        create_product_backlog_item(
            project="MyProject",
            title="Implement user login",
            assigned_to="john.doe@company.com",
            description="<div>Add login functionality to allow users to authenticate.</div>",
            acceptance_criteria="<div>- User can log in with email/password<br/>- Invalid credentials show error</div>",
            area_path="MyProject\\Authentication",
            priority=2
        )
    """
    url = (
        f"{ADO_ORG_URL}/{project}/_apis/wit/workitems/$Product%20Backlog%20Item"
        f"?api-version=7.1-preview.3"
    )

    # Build the JSON Patch document for work item creation
    # Azure DevOps uses JSON Patch format for work item operations
    operations = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title,
        }
    ]

    if description is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.Description",
            "value": description,
        })

    if acceptance_criteria is not None:
        operations.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
            "value": acceptance_criteria,
        })

    if area_path is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path,
        })

    if iteration_path is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path,
        })

    # assigned_to is required
    operations.append({
        "op": "add",
        "path": "/fields/System.AssignedTo",
        "value": assigned_to,
    })

    if priority is not None:
        operations.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": priority,
        })

    if tags is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": tags,
        })

    # Azure DevOps work item API requires application/json-patch+json content type
    headers = {"Content-Type": "application/json-patch+json"}

    resp = client.post(url, json=operations, headers=headers)
    resp.raise_for_status()

    work_item = resp.json()

    # Extract relevant fields from the response
    fields = work_item.get("fields", {})

    return {
        "id": work_item.get("id"),
        "url": work_item.get("_links", {}).get("html", {}).get("href"),
        "title": fields.get("System.Title"),
        "state": fields.get("System.State"),
        "assignedTo": (fields.get("System.AssignedTo") or {}).get("displayName"),
        "areaPath": fields.get("System.AreaPath"),
        "iterationPath": fields.get("System.IterationPath"),
    }


@mcp.tool()
def create_bug(
    project: str,
    title: str,
    assigned_to: str,
    description: str,
    steps_to_reproduce: str,
    expected_behavior: str,
    environment: str = "Dev",
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    priority: Optional[int] = None,
    tags: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new Bug work item in Azure DevOps (using custom "Bugs" type).

    IMPORTANT: Before calling this tool, the LLM MUST:
    1. Call list_projects() to get available projects
    2. Ask the user to choose a project if not specified

    Parameters:
    -----------
    project : str
        REQUIRED. The project name where the bug will be created.
        Use list_projects() to discover available projects.

    title : str
        REQUIRED. The title of the bug. Should be a concise summary of the issue.

    assigned_to : str
        REQUIRED. The email address or display name of the person to assign the bug to.

    description : str
        REQUIRED. Detailed description of the bug. Supports HTML formatting.

    steps_to_reproduce : str
        REQUIRED. Steps to reproduce the bug. Supports HTML formatting.
        Example: "1. Go to login page\\n2. Enter invalid password\\n3. Click submit"

    expected_behavior : str
        REQUIRED. What should happen (the expected app behavior). Supports HTML formatting.
        Example: "User should see an error message indicating invalid credentials"

    environment : str, optional
        The environment where the bug was found. Default is "Dev".
        Common values: "Dev", "Test", "Staging", "Prod"

    area_path : str, optional
        The area path for organizing the bug (e.g., "MyProject\\Team A\\Frontend").
        Use list_area_paths(project) to discover available paths.

    iteration_path : str, optional
        The iteration/sprint path (e.g., "MyProject\\Sprint 1").
        Use list_iteration_paths(project) to discover available paths.

    priority : int, optional
        The priority of the bug (typically 1-4, where 1 is highest priority).

    tags : str, optional
        Semicolon-separated tags (e.g., "regression;production;ui").

    Returns:
    --------
    Dict[str, Any]
        A dictionary containing the created bug details:
        - id: The work item ID
        - url: Direct URL to the work item
        - title: The title
        - state: The initial state (usually "New")
        - assignedTo: The person assigned
        - areaPath: The area path
        - iterationPath: The iteration path

    Example Usage:
    --------------
    The LLM should:
    1. Call list_projects() first
    2. Ask user to choose a project
    3. Then call create_bug with the chosen project

    Example call:
        create_bug(
            project="MyProject",
            title="Login fails with valid credentials",
            assigned_to="john.doe@company.com",
            description="When users try to log in with valid credentials, the login fails silently.",
            steps_to_reproduce="1. Go to /login\\n2. Enter valid credentials\\n3. Click Login",
            expected_behavior="User should be logged in and redirected to dashboard",
            environment="Prod",
            priority=1
        )
    """
    # Use custom "Bugs" work item type (not standard "Bug")
    url = (
        f"{ADO_ORG_URL}/{project}/_apis/wit/workitems/$Bugs"
        f"?api-version=7.1-preview.3"
    )

    operations = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title,
        }
    ]

    # assigned_to is required
    operations.append({
        "op": "add",
        "path": "/fields/System.AssignedTo",
        "value": assigned_to,
    })

    # Description is required for Bugs type
    operations.append({
        "op": "add",
        "path": "/fields/System.Description",
        "value": description,
    })

    # Custom required fields for "Bugs" type
    operations.append({
        "op": "add",
        "path": "/fields/Custom.Environment",
        "value": environment,
    })

    operations.append({
        "op": "add",
        "path": "/fields/Custom.Stepstoreproduce",
        "value": steps_to_reproduce,
    })

    operations.append({
        "op": "add",
        "path": "/fields/Custom.Expectedappbehavior",
        "value": expected_behavior,
    })

    if area_path is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path,
        })

    if iteration_path is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path,
        })

    if priority is not None:
        operations.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": priority,
        })

    if tags is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": tags,
        })

    headers = {"Content-Type": "application/json-patch+json"}

    resp = client.post(url, json=operations, headers=headers)

    # Better error handling to see Azure DevOps error details
    if resp.status_code >= 400:
        try:
            error_detail = resp.json()
        except Exception:
            error_detail = resp.text
        raise Exception(f"Azure DevOps API error {resp.status_code}: {error_detail}")

    bug_item = resp.json()
    bug_fields = bug_item.get("fields", {})

    return {
        "id": bug_item.get("id"),
        "url": bug_item.get("_links", {}).get("html", {}).get("href"),
        "title": bug_fields.get("System.Title"),
        "state": bug_fields.get("System.State"),
        "assignedTo": (bug_fields.get("System.AssignedTo") or {}).get("displayName"),
        "areaPath": bug_fields.get("System.AreaPath"),
        "iterationPath": bug_fields.get("System.IterationPath"),
    }


@mcp.tool()
def create_work_item(
    project: str,
    work_item_type: str,
    title: str,
    assigned_to: str,
    description: Optional[str] = None,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
    priority: Optional[int] = None,
    tags: Optional[str] = None,
    custom_fields: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create a work item of ANY type in Azure DevOps.

    Use this tool when you need flexibility in work item type. This is the recommended
    tool for creating work items because it works with any process template.

    IMPORTANT WORKFLOW:
    1. Call list_projects() to get available projects
    2. Call list_work_item_types(project) to see what types exist
    3. Call this tool with the correct work_item_type

    Common work item types by process template:
    - Basic: Epic, Issue, Task
    - Scrum: Epic, Feature, Product Backlog Item, Bug, Task
    - Agile: Epic, Feature, User Story, Bug, Task
    - CMMI: Epic, Feature, Requirement, Bug, Task

    DECISION GUIDE for LLM:
    - Branch contains "fix/" or "bug/" or "hotfix/" → use "Bug" or "Bugs" or "Issue"
    - Branch contains "feature/" → use "Product Backlog Item" or "User Story" or "Issue"
    - If creation fails with 400 error showing required fields → use custom_fields parameter

    Parameters:
    -----------
    project : str
        REQUIRED. The project name.

    work_item_type : str
        REQUIRED. The work item type name exactly as returned by list_work_item_types().
        Examples: "Bug", "Bugs", "Issue", "Product Backlog Item", "User Story", "Task"

    title : str
        REQUIRED. The title of the work item.

    assigned_to : str
        REQUIRED. Email or display name of the assignee.

    description : str, optional
        Description of the work item. Supports HTML.
        NOTE: For "Bugs" type, this is REQUIRED.

    area_path : str, optional
        Area path for organizing the work item.

    iteration_path : str, optional
        Sprint/iteration path.

    priority : int, optional
        Priority (1-4, where 1 is highest).

    tags : str, optional
        Semicolon-separated tags.

    custom_fields : Dict[str, str], optional
        Dictionary of custom field reference names to values.
        Use this for project-specific required fields.

        For UnravelEXT "Bugs" type, required custom fields:
        {
            "Custom.Environment": "Dev|Test|Prod",
            "Custom.Stepstoreproduce": "Steps to reproduce the bug",
            "Custom.Expectedappbehavior": "What should happen"
        }

    Returns:
    --------
    Dict with: id, url, title, state, workItemType, assignedTo, areaPath, iterationPath

    Example for standard work item:
        create_work_item(
            project="MyProject",
            work_item_type="Product Backlog Item",
            title="Add login feature",
            assigned_to="john@company.com",
            description="Implement user login"
        )

    Example for custom "Bugs" type with required fields:
        create_work_item(
            project="UnravelEXT",
            work_item_type="Bugs",
            title="Fix login error",
            assigned_to="john@company.com",
            description="Login button not working",
            custom_fields={
                "Custom.Environment": "Dev",
                "Custom.Stepstoreproduce": "1. Go to login\\n2. Click submit",
                "Custom.Expectedappbehavior": "User should be logged in"
            }
        )
    """
    # URL-encode the work item type (spaces become %20)
    encoded_type = work_item_type.replace(" ", "%20")

    url = (
        f"{ADO_ORG_URL}/{project}/_apis/wit/workitems/${encoded_type}"
        f"?api-version=7.1-preview.3"
    )

    operations = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title,
        }
    ]

    # assigned_to is required
    operations.append({
        "op": "add",
        "path": "/fields/System.AssignedTo",
        "value": assigned_to,
    })

    if description is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.Description",
            "value": description,
        })

    if area_path is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path,
        })

    if iteration_path is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path,
        })

    if priority is not None:
        operations.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": priority,
        })

    if tags is not None:
        operations.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": tags,
        })

    # Add custom fields if provided (for project-specific required fields)
    if custom_fields is not None:
        for field_name, field_value in custom_fields.items():
            operations.append({
                "op": "add",
                "path": f"/fields/{field_name}",
                "value": field_value,
            })

    headers = {"Content-Type": "application/json-patch+json"}

    resp = client.post(url, json=operations, headers=headers)

    # Better error handling to see Azure DevOps error details
    if resp.status_code >= 400:
        try:
            error_detail = resp.json()
        except Exception:
            error_detail = resp.text
        raise Exception(f"Azure DevOps API error {resp.status_code}: {error_detail}")

    work_item = resp.json()
    fields = work_item.get("fields", {})

    return {
        "id": work_item.get("id"),
        "url": work_item.get("_links", {}).get("html", {}).get("href"),
        "title": fields.get("System.Title"),
        "state": fields.get("System.State"),
        "workItemType": fields.get("System.WorkItemType"),
        "assignedTo": (fields.get("System.AssignedTo") or {}).get("displayName"),
        "areaPath": fields.get("System.AreaPath"),
        "iterationPath": fields.get("System.IterationPath"),
    }