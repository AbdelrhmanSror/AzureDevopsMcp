"""Repository-related MCP tools."""
from ..config import mcp
from ..utils.helpers import resolve_repo_id_internal


@mcp.tool()
def resolve_repo_id(repo_key: str) -> str:
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
