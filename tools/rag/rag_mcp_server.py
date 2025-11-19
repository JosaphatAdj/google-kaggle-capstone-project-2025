"""
Configuration pour serveur MCP RAG dédié (future extension)
"""
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Pour future implémentation d'un serveur MCP RAG dédié
rag_mcp_server = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["-m", "tools.rag.rag_mcp_server"],
        ),
        timeout=30,
    )
)