
import os
import requests
from dotenv import load_dotenv



# Load environment variables from .env file in the workspace (if present)
load_dotenv()


# Program-wide MCP connection configuration
# These variables can be set in your .env file or system environment
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'https://mcp.ai.juniper.net/mcp/mist')
MCP_API_TOKEN = os.getenv('MCP_API_TOKEN', os.getenv('MIST_API_TOKEN', 'YOUR_MIST_API_TOKEN'))
MCP_ORG_ID = os.getenv('MCP_ORG_ID', os.getenv('org_id', None))
MCP_BASE_URL = os.getenv('MCP_BASE_URL', os.getenv('MIST_HOST', 'https://api.mist.com'))

HEADERS = {
    'Authorization': f'Bearer {MCP_API_TOKEN}',
    'X-Mist-Base-URL': MCP_BASE_URL
}
if MCP_ORG_ID:
    HEADERS['X-Mist-Org-ID'] = MCP_ORG_ID


def call_mcp_server(endpoint: str, method: str = 'GET', params=None, data=None):
    """
    Calls the configured MCP server endpoint with the correct headers.
    The MCP server URL, token, and org ID are set via environment variables for program-wide switching.
    """
    url = f"{MCP_SERVER_URL}{endpoint}"
    response = requests.request(method, url, headers=HEADERS, params=params, json=data)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Test MCP server root endpoint
    try:
        root_response = call_mcp_server('/')
        print("Root endpoint response:", root_response)
    except Exception as e:
        print("Error communicating with MCP server root endpoint:", e)

    # Example: Get org info
    try:
        orgs = call_mcp_server('/orgs')
        print("Organizations:", orgs)
    except Exception as e:
        print("Error communicating with MCP server /orgs:", e)
