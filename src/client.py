"""HTTP client for Azure DevOps API."""
import httpx
from .config import ADO_PAT

auth = ("", ADO_PAT)
client = httpx.Client(auth=auth)
