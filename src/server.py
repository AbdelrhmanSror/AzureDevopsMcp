"""Main MCP server entry point."""
from .config import mcp


def main():
    """Entry point for the MCP server."""
    # Import all modules to trigger tool/resource registration
    from . import tools  # noqa: F401
    from . import policies  # noqa: F401

    mcp.run(transport="stdio")

    # Alternative: HTTP / streamable MCP server
    # mcp.run(
    #     transport="streamable-http",
    #     host="127.0.0.1",
    #     port=8000,
    #     path="/mcp",
    # )


if __name__ == "__main__":
    main()
