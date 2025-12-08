"""Configuration management for Azure DevOps MCP server."""
import os
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# Global MCP instance - accessible everywhere
mcp = FastMCP("azure-devops-pr")

# Azure DevOps configuration
ADO_ORG_URL = os.getenv("ADO_ORG_URL")
ADO_PROJECT = os.getenv("ADO_PROJECT")
ADO_PAT = os.getenv("ADO_PAT")  # PAT with Code / PR permissions

if not all([ADO_ORG_URL, ADO_PROJECT, ADO_PAT]):
    raise SystemExit("Missing env vars: ADO_ORG_URL / ADO_PROJECT / ADO_PAT")
