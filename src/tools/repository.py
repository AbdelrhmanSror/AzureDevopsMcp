"""Repository-related MCP tools."""
from typing import List, Dict, Any, Optional
from ..config import mcp, ADO_ORG_URL
from ..client import client
from ..utils.helpers import resolve_repo_id_internal


@mcp.tool()
def list_projects() -> List[Dict[str, Any]]:
    """
    List all Azure DevOps projects you have access to.

    Call this tool BEFORE creating work items (PBI, Bug) to discover available projects.
    The LLM should prompt the user to choose a project from the list.

    Returns:
    --------
    List[Dict[str, Any]]
        A list of projects, each containing:
        - name: The project name (use this for create_product_backlog_item, create_bug)
        - id: The project GUID
        - description: Project description
        - state: Project state (e.g., "wellFormed")

    Example Usage:
    --------------
    Call this when the user wants to create a work item:
        "Create a PBI" → First call list_projects() and ask user to choose
        "What projects do I have access to?"
        "Show me available projects"
    """
    url = f"{ADO_ORG_URL}/_apis/projects?api-version=7.1-preview.4"

    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    projects = data.get("value", [])

    result: List[Dict[str, Any]] = []
    for proj in projects:
        result.append({
            "name": proj.get("name"),
            "id": proj.get("id"),
            "description": proj.get("description"),
            "state": proj.get("state"),
        })

    return result


@mcp.tool()
def resolve_repo_id(repo_key: str, project: Optional[str] = None) -> str:
    """
        Resolve an Azure DevOps Git repository identifier into a canonical GUID.

        This tool exists because many other tools in this MCP server expect a **repositoryId GUID**,
        while humans (and UIs) usually work with the **repository name**.

        Behavior:
        - If `repo_key` already looks like a GUID (36-char hex with dashes), it is returned as-is.
        - Otherwise, the tool calls the Azure DevOps "list repositories" API for the configured
          `ADO_PROJECT` and tries to find a repository whose `name` matches `repo_key` exactly.
        - If a matching repo is found, its `id` (GUID) is returned.
        - If no repo is found, the tool raises an error (the MCP host will see this as a failure).

        Parameters:
        - repo_key: Either the human-friendly repository name (e.g. "road-api") or the
          repository GUID (e.g. "7c9a1f2e-1234-4d5e-9abc-0f1122334455").

        Returns:
        - A string containing the **repository GUID** that can be safely passed to other tools
          like `list_pull_requests`, `get_pull_request`, and `get_pull_request_full_diff`.

        Typical usage pattern for an LLM:
        1. When the user mentions a repo by name, call `resolve_repo_id(repo_key="<name>")`.
        2. Use the returned GUID as `repo_id` in subsequent tools.
    """
    return resolve_repo_id_internal(repo_key)


@mcp.tool()
def list_branches(
    repo_id: str,
    filter_name: Optional[str] = None,
    top: int = 100,
) -> List[Dict[str, Any]]:
    """
    List branches in an Azure DevOps Git repository.

    Call this tool BEFORE creating a PR to discover available branches for
    source_branch and target_branch parameters.

    Parameters:
    -----------
    repo_id : str
        The repository GUID returned by `resolve_repo_id`.

    filter_name : str, optional
        Filter branches by name prefix (e.g., "feature/" to list only feature branches).
        Case-insensitive partial match.

    top : int, optional
        Maximum number of branches to return. Default is 100.

    Returns:
    --------
    List[Dict[str, Any]]
        A list of branches, each containing:
        - name: Short branch name (e.g., "main", "feature/login")
        - fullName: Full ref name (e.g., "refs/heads/main") - use this for create_pull_request
        - isDefault: True if this is the default branch
        - creator: Display name of the person who created the branch
        - aheadCount: Number of commits ahead of the default branch (if available)
        - behindCount: Number of commits behind the default branch (if available)

    Example Usage:
    --------------
    Call this when the user wants to create a PR or see available branches:
        "What branches are available?"
        "Show me feature branches"
        "Create a PR from my branch to main"

    Example call:
        list_branches(repo_id="<guid>")
        list_branches(repo_id="<guid>", filter_name="feature/")
    """
    url = (
        f"{ADO_ORG_URL}/_apis/git/repositories/{repo_id}/refs"
        f"?filter=heads/&$top={top}&api-version=7.1-preview.1"
    )

    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    refs = data.get("value", [])

    result: List[Dict[str, Any]] = []

    for ref in refs:
        full_name = ref.get("name", "")
        # Extract short name from refs/heads/xxx
        short_name = full_name.replace("refs/heads/", "") if full_name.startswith("refs/heads/") else full_name

        # Apply filter if specified
        if filter_name and filter_name.lower() not in short_name.lower():
            continue

        creator = ref.get("creator", {})

        result.append({
            "name": short_name,
            "fullName": full_name,
            "isDefault": ref.get("isDefault", False),
            "creator": creator.get("displayName") if creator else None,
            "objectId": ref.get("objectId"),  # commit SHA
        })

    return result
