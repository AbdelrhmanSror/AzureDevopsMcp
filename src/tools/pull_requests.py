"""Pull request-related MCP tools."""
from typing import Dict, Any, List, Optional
from ..config import mcp, ADO_ORG_URL, ADO_PROJECT
from ..client import client
from ..utils.helpers import get_latest_iteration_id, get_blob_text


@mcp.tool()
def list_pull_requests(
        repo_id: str,
        status: str = "active",
        top: int = 10,
) -> List[Dict[str, Any]]:
    """
        List pull requests for a specific Azure DevOps repository and return structured metadata.

        This tool is the **entry point** for discovering which PRs exist in a repo so that the
        LLM (or user) can decide which one to inspect or review in more detail.

        It queries the Azure DevOps "list pull requests" API for the configured organization
        and project, filtered to the given repository and status.

        Parameters:
        - repo_id:
            The **repository GUID** returned by `resolve_repo_id`. Do not pass the repo name here
            unless you are 100% sure it is already a GUID.
        - status:
            Filter for PR status. Common values:
              - "active"   → open PRs that are under review (default)
              - "completed"→ merged/closed PRs
              - "abandoned"→ explicitly abandoned PRs
            The string is passed directly to Azure DevOps as `searchCriteria.status`.
        - top:
            Maximum number of PRs to return. This is useful to avoid overwhelming the LLM with
            a very large list. Defaults to 10.

        Returns:
        - A list of dictionaries. Each dictionary has the structure:
            {
              "id": <int>,               # pullRequestId
              "title": <str>,
              "status": <str>,           # e.g. "active", "completed"
              "createdBy": <str>,        # display name of the author
              "repoName": <str>,         # human repo name
              "sourceBranch": <str>,     # e.g. "refs/heads/feature/foo"
              "targetBranch": <str>,     # e.g. "refs/heads/main"
            }

        How an LLM should use this:
        - Call this tool when the user says things like:
            "Show me the open PRs for road-api"
            "List the last few PRs in this repo"
        - Present the results to the user in a readable table or list.
        - When the user picks a PR (by `id` or title), pass its `id` into `get_pull_request`
          or `get_pull_request_full_diff` for deeper inspection.
    """
    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}/_apis/git/pullrequests"
        f"?searchCriteria.repositoryId={repo_id}"
        f"&searchCriteria.status={status}"
        f"&$top={top}"
        f"&api-version=7.1-preview.1"
    )

    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    prs = data.get("value", [])

    if not prs:
        return []

    result: List[Dict[str, Any]] = []
    for pr in prs:
        result.append(
            {
                "id": pr["pullRequestId"],
                "title": pr["title"],
                "status": pr["status"],
                "createdBy": pr["createdBy"]["displayName"],
                "repoName": pr["repository"]["name"],
                "sourceBranch": pr.get("sourceRefName", ""),
                "targetBranch": pr.get("targetRefName", ""),
            }
        )

    return result


@mcp.tool()
def get_pull_request(repo_id: str, pr_id: int) -> str:
    """
        Retrieve detailed, human-readable information about a specific pull request.

        This tool fetches the full PR metadata from Azure DevOps and returns it formatted
        as a multi-line text block. It is intended to give the LLM a high-level, human
        description of the PR before doing deeper analysis (like reading the diff).

        Parameters:
        - repo_id:
            The **repository GUID** returned by `resolve_repo_id`.
        - pr_id:
            The numeric pull request ID (e.g. 8373) as returned by `list_pull_requests`
            under the `"id"` key.

        Returns:
        - A formatted string that includes:
            - PR number and title
            - Status (active/completed/abandoned)
            - Author (display name + unique name/email where available)
            - Source and target branches
            - The PR description/body text

        Recommended LLM usage:
        - After listing PRs, call this tool on the PR the user is interested in.
        - Use the returned text to:
            - Summarize the purpose and scope of the PR in simpler language.
            - Explain to the user what the PR is about and what it changes conceptually.
            - Decide whether a full code diff analysis (`get_pull_request_full_diff`) is needed.
    """
    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/pullrequests/{pr_id}?api-version=7.1-preview.1"
    )
    resp = client.get(url)
    resp.raise_for_status()
    pr = resp.json()

    details = (
        f"PR #{pr['pullRequestId']}: {pr['title']}\n"
        f"Status: {pr['status']}\n"
        f"CreatedBy: {pr['createdBy']['displayName']} ({pr['createdBy'].get('uniqueName', '')})\n"
        f"SourceBranch: {pr.get('sourceRefName', '')}\n"
        f"TargetBranch: {pr.get('targetRefName', '')}\n"
        f"Description:\n{pr.get('description', '')}\n"
    )

    return details


@mcp.tool()
def get_pull_request_full_diff(repo_id: str, pr_id: int) -> Dict[str, Any]:
    """
        Fetch the full unified diff and all existing review comments for a pull request.

        WHAT THIS TOOL RETURNS
        ----------------------
        This tool returns a dictionary with two keys:

          1) unified_diff:
                A unified-style diff for the latest PR iteration, including full
                ORIGINAL and MODIFIED file contents for each changed file. This is the
                authoritative representation of what changed in the PR.

          2) comments:
                A complete list of review comments on the PR:
                    - file-level comments (with file path + line number)
                    - threaded discussion comments
                    - general PR comments
                Each entry includes author, content, thread information, and status.

        This combined payload provides all context required for a complete code review.

        HOW THE LLM MUST USE THIS TOOL
        ------------------------------
        When performing a PR review, the LLM must follow this sequence:

        1. **Call `get_review_policy()` first.**
           The review policy defines the mandatory conventions, expectations, and
           evaluation criteria for this repository.
           The LLM is required to load and apply these rules before analyzing any diff.

        2. **Use this tool (`get_pull_request_full_diff`) to retrieve the actual code changes**
           and all PR comments. The unified diff returned here is the single source of truth
           for what changed. Do not infer behavior that is not visible in the diff.

        3. **Use the PR comments** to:
              - Understand existing feedback from human reviewers.
              - Avoid repeating concerns already raised.
              - Identify unresolved or overlooked issues.
              - Detect patterns in reviewer concerns.

        4. **Combine:**
              - review policy → rules + standards
              - unified diff → ground-truth code changes
              - PR comments → reviewer context
              - PR metadata (from `get_pull_request()`) → intent

           to produce a structured, high-quality, human-like code review.

        EXPECTED REVIEW BEHAVIOR
        ------------------------
        After loading the review policy, the LLM must:

        - Follow *all* policy rules when evaluating schema design, validation logic,
          service-layer behavior, API-layer practices, documentation quality, and tests.
        - Provide old vs new code comparisons for meaningful changes.
        - Identify missing tests, missing docstrings, unclear code, anti-patterns,
          inconsistencies, or violations of established conventions.
        - Produce a professional, actionable review in the format defined by the policy
          (e.g., Summary, Key Changes, Schema Review, API Review, Service Layer, Validation,
          Docs, Tests & Coverage, Suggestions).

        NOTES
        -----
        - The diff always represents the latest PR iteration.
        - Comments include active, resolved, and general PR discussions.
        - This tool is typically used together with:
              • get_review_policy()        — required before generating the review
              • get_pull_request()         — provides PR metadata
        - The LLM must treat the review policy as binding and must not skip any required sections.
    """

    # 1. Get latest iteration id
    iteration_id = get_latest_iteration_id(repo_id, pr_id)

    # 2. Fetch changes for that iteration
    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/pullRequests/{pr_id}/iterations/{iteration_id}/changes"
        f"?api-version=7.1-preview.1&$top=1000"
    )

    resp = client.get(url)
    resp.raise_for_status()

    data = resp.json()
    entries = data.get("changeEntries") or data.get("changes") or []

    unified_parts: List[str] = []

    if not entries:
        diff_text = f"No change entries found for PR #{pr_id}."
    else:
        for change in entries:
            if not isinstance(change, dict):
                continue

            item = change.get("item") or {}
            path = item.get("path", "<unknown-path>")
            change_type = change.get("changeType", "?")

            # object IDs are under item
            original_id = item.get("originalObjectId")  # may be None for added files
            new_id = item.get("objectId")  # current version

            original_text = get_blob_text(repo_id, original_id) if original_id else ""
            modified_text = get_blob_text(repo_id, new_id) if new_id else ""

            unified_parts.append(
                f"--- a{path}\n"
                f"+++ b{path}\n"
                f"@@ {change_type} {path} @@\n"
                f"--- ORIGINAL ---\n{original_text}\n"
                f"--- MODIFIED ---\n{modified_text}\n"
            )

        diff_text = "\n".join(unified_parts)

    # 3. Fetch all PR threads (comments)
    threads_url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/pullRequests/{pr_id}/threads"
        f"?api-version=7.1-preview.1"
    )

    threads_resp = client.get(threads_url)
    threads_resp.raise_for_status()
    threads_data = threads_resp.json()
    threads = threads_data.get("value", [])

    comments_out: List[Dict[str, Any]] = []

    for thread in threads:
        thread_context = thread.get("threadContext") or {}
        file_path = thread_context.get("filePath")
        line = None

        right_start = thread_context.get("rightFileStart") or {}
        left_start = thread_context.get("leftFileStart") or {}

        if right_start.get("line") is not None:
            line = right_start.get("line")
        elif left_start.get("line") is not None:
            line = left_start.get("line")

        thread_status = thread.get("status")
        thread_id = thread.get("id")

        for c in thread.get("comments", []):
            comments_out.append(
                {
                    "file": file_path,
                    "line": line,
                    "content": c.get("content"),
                    "author": (c.get("author") or {}).get("displayName"),
                    "status": thread_status,
                    "threadId": thread_id,
                    "commentId": c.get("id"),
                }
            )

    return {
        "diff": diff_text,
        "comments": comments_out,
    }


@mcp.tool()
def add_pull_request_comment(
        repo_id: str,
        pr_id: int,
        comment: str,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
) -> str:
    """
        Add a comment to a pull request.

        If `file_path` and `line` are provided, the comment will be created as an
        inline thread on that file and line in the latest diff.

        If `file_path` and `line` are omitted, the comment will be created as a
        top-level PR thread (not attached to a specific file).
    """
    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/pullRequests/{pr_id}/threads"
        f"?api-version=7.1-preview.1"
    )

    thread_context = None
    if file_path is not None and line is not None:
        # Attach comment to a specific file and line on the RIGHT (modified) side
        thread_context = {
            "filePath": file_path,
            "rightFileStart": {"line": line, "offset": 1},
            "rightFileEnd": {"line": line, "offset": 1},
        }

    payload = {
        "comments": [
            {
                "parentCommentId": 0,
                "content": comment,
                "commentType": 1,  # text
            }
        ],
        "status": 1,  # active
    }

    if thread_context is not None:
        payload["threadContext"] = thread_context

    resp = client.post(url, json=payload)
    resp.raise_for_status()

    data = resp.json()
    thread_id = data.get("id")
    return f"Comment posted in thread id {thread_id}"

@mcp.tool()
def set_pr_description(repo_id: str, pr_id: int, description_markdown: str) -> Dict[str, Any]:
    """
    Update the Azure DevOps PR description with the provided Markdown text.

    ──────────────────────────────────────────────────────────────────────────────
    IMPORTANT: REQUIRED WORKFLOW FOR THE LLM
    ──────────────────────────────────────────────────────────────────────────────
    This tool MUST NOT be called until the LLM has done ALL of the following:

      1. Read the full diff using: get_pull_request_full_diff
      2. Load and read the PR description guide text from:
            PR_DESCRIPTION_GUIDE
         (included in this tool’s docstring for safety)
      3. Construct a **concise, high-level** PR description following EXACTLY the
         structure and rules defined in the PR description guide.
      4. Ensure the description focuses on **why** the PR exists and the **top 1–2
         visible effects** of the change — NOT implementation details.

    If the LLM has not followed steps 1–4, it must NOT call this tool.


    ──────────────────────────────────────────────────────────────────────────────
    PR DESCRIPTION GUIDE (Embedded for safety)
    ──────────────────────────────────────────────────────────────────────────────
    ## What type of PR is this? (check all applicable)
    - [ ] Refactor
    - [ ] Feature
    - [ ] Bug Fix
    - [ ] Platform related
    - [ ] Documentation Update

    ## Description
    This section must be **very short and to the point**.

    Rules:
      • Describe **why** the PR exists.
      • Give a **high-level summary** of the main change.
      • Max length: **1 short sentence + 1–2 bullets** (or 3 lines total).
      • NEVER restate the diff or describe the code internally.
      • Avoid long paragraphs, unnecessary details, and explaining the algorithm.

    Example good descriptions:
      • "Fixes incorrect problem field mapping so the frontend receives the right structure."
      • "Adds a typed endpoint to expose problem fields for the UI."
      • "Refactors field extraction logic into a dedicated service to simplify updates."

    ## Test Instructions
      • Explain briefly how a reviewer or QA can verify the change.
      • List key pytest commands or a short manual step if required.
      • Keep it minimal and practical.

    ## Added/updated tests?
    - [ ] Yes
    - [ ] No, because: <brief explanation>
    - [ ] I need help with writing tests

    ## Added/updated Code Documentation?
    - [ ] Yes
    - [ ] No, because: <brief explanation>

    General principles:
      • Be concise.
      • Lead with **WHY**, not HOW.
      • Highlight only the most important aspects.
      • Assume reviewers can see the diff.
      • Shorter is better.


    ──────────────────────────────────────────────────────────────────────────────
    PURPOSE OF THIS TOOL
    ──────────────────────────────────────────────────────────────────────────────
    Once the LLM generates a description that follows the rules above,
    this tool sends that Markdown to Azure DevOps to update the PR.


    RETURNS
    -------
    A small summary of the updated PR, including:
      - id
      - status
      - title
      - description
    """


    url = (
        f"{ADO_ORG_URL}/{ADO_PROJECT}"
        f"/_apis/git/repositories/{repo_id}/pullRequests/{pr_id}"
        f"?api-version=7.1-preview.1"
    )

    payload = {
        "description": description_markdown,
    }

    resp = client.patch(url, json=payload)
    resp.raise_for_status()

    pr = resp.json()

    # Return a small summary so the LLM/user can confirm the update
    return {
        "id": pr.get("pullRequestId") or pr.get("id"),
        "status": pr.get("status"),
        "title": pr.get("title"),
        "description": pr.get("description"),
    }
