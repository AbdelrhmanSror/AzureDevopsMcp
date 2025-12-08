"""Review policy resource for Azure DevOps MCP server."""
from ..config import mcp

REVIEW_POLICY_TEXT = """
OFFICIAL CODE REVIEW POLICY
===========================

All pull request reviews must adhere to the following engineering standards.  
These rules define how reviewers evaluate correctness, maintainability, clarity,
and alignment with established conventions in this repository.

1) SCHEMA & MODEL DESIGN
------------------------
- Client-facing models must be explicit, well-typed, and avoid ambiguous structures
  such as Dict[str, Any] where a more precise model is possible.
- Response models must reflect the actual output of the service layer.
- Example data in schema_extra must match the true runtime format.
- All schema fields must include clear, meaningful descriptions explaining their purpose.
- Naming conventions must follow project standards (e.g., *Schema suffix).
- Avoid redundant alias definitions unless the alias differs from the field name.

2) VALIDATION RULES
-------------------
- Validation logic belongs in schemas or the domain layer, not in API endpoints.
- Lists that are required must validate non-emptiness.
- Domain-specific errors (e.g., BadRequestError) must be raised for invalid inputs.
- Do not re-implement validation that Pydantic already guarantees (e.g., Literal, Regex).

3) API LAYER EXPECTATIONS
-------------------------
- API docstrings must follow the project's structured format, including purpose,
  parameters, returns, and error behavior.
- Logging decorators must be applied consistently across endpoints.
- The API layer should contain minimal logic; services or schemas should hold all
  business rules.
- Avoid unnecessary transformations when validation already guarantees correctness.
- Endpoint naming, ordering, and style must follow established patterns.

4) SERVICE LAYER PRINCIPLES
---------------------------
- Service classes should follow the Single Responsibility Principle.
- Complex operations should be broken into private helper methods for clarity and reuse.
- Avoid fallback chains that mask missing data; required fields should be accessed
  directly so integrity issues surface early.
- Use precise types (e.g., Set[Literal[...]] or shared type definitions) rather than
  general string sets.
- Repeated transformations (e.g., wrapping values) should be extracted into reusable
  helper functions.

5) CODE QUALITY & READABILITY
-----------------------------
- Code should be self-explanatory. If a comment explains obvious behavior, refactor the
  code instead of adding comments.
- Naming should be descriptive, consistent, and aligned with the rest of the project.
- Avoid code duplication; refactor out shared patterns.
- The flow of logic should be clear, linear, and predictable.
- Follow established design patterns used across this codebase.

6) DOCSTRINGS & DOCUMENTATION
-----------------------------
- Every new public function, class, or module must include a complete docstring.
- Docstrings must describe purpose, parameters, return values, error conditions, and
  notable behavior.
- Schema fields should include detailed explanations for API consumers.
- Documentation must be consistent with actual behavior.

7) TESTING REQUIREMENTS
------------------------
- API-layer tests validate response structure, not business logic values.
- Service-layer tests must verify logic correctness, edge cases, and error behavior.
- Every non-trivial behavioral change must be accompanied by new or updated tests.
- Missing tests must be called out clearly, with suggestions for what to test
  (success paths, failure paths, edge cases).
- Tests must follow the existing testing style and structure.

8) REVIEW STYLE & EXPECTATIONS
------------------------------
Reviews must be structured, actionable, and written in a professional teammate tone.
Every review must include:

- Summary of the PR's purpose and scope.
- Old vs new code snippets for key logic changes.
- Detailed analysis by category:
    * Schema & Models
    * API Layer
    * Service Layer
    * Validation Logic
    * Documentation / Docstrings
    * Testing & Coverage
    * Readability & Maintainability
- A final section with clear recommendations and action items.

9) SOURCE OF TRUTH
------------------
All code review conclusions must be based strictly on:
- The unified diff returned by the diff tool
- The existing review comments retrieved from the PR
- The rules defined in this policy

Reviewers must not infer functionality that is not visible in the diff.

This policy must be followed for every automated and manual review.
It defines the engineering bar for contributions to this repository.
"""


@mcp.resource(
    uri="policy://review",
    name="Review Policy",
    description="Official PR review policy that the LLM must follow when reviewing pull requests.",
)
def get_review_policy() -> str:
    """
    Provides the official PR review policy text for this repository.
    The client or LLM should load this resource before performing any PR review.
    """
    return REVIEW_POLICY_TEXT
