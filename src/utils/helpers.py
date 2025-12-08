"""Helper functions for Azure DevOps operations."""
import re
from typing import Optional
from ..client import client
from ..config import ADO_ORG_URL, ADO_PROJECT


def resolve_repo_id_internal(repo_key: str) -> str:
    """
    If repo_key is already a GUID -> return as-is.
    If repo_key is a name -> call /repositories and find the matching repo, return its id.
    """
    # Very simple GUID check
    if re.fullmatch(r"[0-9a-fA-F-]{36}", repo_key):
        return repo_key

    url = f"{ADO_ORG_URL}/{ADO_PROJECT}/_apis/git/repositories?api-version=7.1-preview.1"
    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    for repo in data.get("value", []):
        if repo["name"] == repo_key:
            return repo["id"]

    raise RuntimeError(f"Could not find repository with name '{repo_key}' in project '{ADO_PROJECT}'")


def get_latest_iteration_id(repo_id: str, pr_id: int) -> int:
    """Get the latest iteration id for a pull request."""
    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/pullRequests/{pr_id}/iterations"
        f"?api-version=7.1-preview.1"
    )
    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    iterations = data.get("value", [])
    if not iterations:
        raise RuntimeError(f"No iterations found for PR #{pr_id}")

    latest = iterations[-1]
    iteration_id = latest["id"]
    return iteration_id


def get_blob_text(repo_id: str, object_id: Optional[str]) -> str:
    """Fetch the raw text content of a blob (file version) by its object ID."""
    if not object_id:
        return ""

    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/blobs/{object_id}"
        f"?api-version=7.1-preview.1&download=true&$format=text"
    )
    resp = client.get(url)
    if resp.status_code != 200:
        return ""

    return resp.text
