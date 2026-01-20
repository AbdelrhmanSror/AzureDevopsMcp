"""Auto-import all tool modules to register them."""
# Import all tool modules - they will auto-register with the global mcp instance
from . import repository  # noqa: F401
from . import pull_requests  # noqa: F401
from . import work_items  # noqa: F401
