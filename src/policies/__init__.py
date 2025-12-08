"""Auto-import all policy/resource modules to register them."""
# Import all policy modules - they will auto-register with the global mcp instance
from . import review_policy  # noqa: F401
