"""Review policy resource for Azure DevOps MCP server."""
from ..config import mcp

REVIEW_POLICY_TEXT = """
LIGHTWEIGHT PR REVIEW POLICY
============================

This policy is designed for **pragmatic, focused code reviews**.
The goal is to catch **meaningful issues** and improve the code where it matters,
without over-reviewing or redesigning the entire solution.

SCOPE OF THE REVIEW
-------------------
- Prioritize **correctness**, **clarity**, and **consistency with existing patterns**.
- Focus on **new or changed code only** as shown in the diff.
- Do **not** attempt a full architecture review unless the PR clearly introduces
  architectural changes.
- Keep feedback **practical and proportionate** to the size and impact of the PR.

WHAT TO ALWAYS CHECK
--------------------
For the changed code, the reviewer should primarily verify:

1) Correctness & Safety
   - Does the new logic do what it claims to do?
   - Are obvious edge cases or error paths handled?
   - Is there any clear risk of crashes, bad data, or security concerns?

2) Readability & Consistency
   - Is the new code understandable without excessive mental effort?
   - Does it follow existing naming, patterns, and structure in this repository?
   - Is there unnecessary duplication that can be easily avoided?

3) Tests (Only for New Behavior)
   - If the PR introduces non-trivial new behavior, is there at least one test
     covering the main happy path and a key edge/error case?
   - API tests should validate response structure; deep logic should be tested
     in the service/domain layer.

4) Docstrings & API Contracts (When Relevant)
   - If new public functions, endpoints, or schemas are added:
       - Is there a minimal but clear docstring or description?
       - Does the documented behavior match what the code actually does?

WHAT TO AVOID
-------------
To prevent over-review, the reviewer should **not**:

- Nitpick personal style preferences that do not violate existing patterns.
- Propose large refactors unless there is a **clear, concrete** benefit
  (e.g., obvious bug risk, major readability problem, or duplication).
- Request changes for minor cosmetic details (spacing, trivial renames, etc.)
  unless they materially improve clarity.
- Reopen topics that are already clearly discussed and resolved in existing comments.

REVIEW OUTPUT STYLE
-------------------
- Keep the review **short and focused**, especially for small PRs.
- Prefer **a few high-impact comments** over many low-value ones.
- When pointing out an issue, include a **specific, actionable suggestion**.
- Use a friendly, teammate tone. The goal is collaboration, not policing.

SUGGESTED REVIEW STRUCTURE
--------------------------
Reviews may follow this simple structure:

- Summary: 2–3 sentences describing what the PR does and overall impression.
- Key Issues (if any): List 2–5 concrete, high-priority observations.
- Optional Nice-to-haves: Only if they are easy wins and clearly beneficial.
- Tests: Briefly note if tests are sufficient, missing, or could use one more case.

SOURCE OF TRUTH
---------------
All conclusions must be based strictly on:
- The unified diff returned by the diff tool.
- Any existing comments on the PR (to avoid duplicating feedback).

Do not assume or speculate about code that is not visible in the diff.

The goal of this policy is to keep reviews **helpful, respectful, and efficient**,
focusing on the changes that really matter.
"""


@mcp.resource(
    uri="policy://review",
    name="Review Policy",
    description="Lightweight PR review policy that keeps feedback focused and avoids over-reviewing.",
)
def get_review_policy() -> str:
    """
    Provides the lightweight PR review policy text for this repository.
    The client or LLM may load this resource before performing any PR review.
    """
    return REVIEW_POLICY_TEXT
