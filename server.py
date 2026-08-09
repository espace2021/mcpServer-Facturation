import asyncio
from fastmcp import FastMCP
from tools import articles_tools, analyse_clients_tools, analyse_reglements_tools,clients_tools

mcp_server = FastMCP("Facturation Server")
mcp_server.mount(articles_tools.mcp)  # ou mcp_server.import_server(articles.mcp) selon ta version de fastmcp
mcp_server.mount(analyse_clients_tools.mcp)
mcp_server.mount(analyse_reglements_tools.mcp)
mcp_server.mount(clients_tools.mcp)

async def main():
    # Lancer le serveur (bloquant)
    await mcp_server.run_async(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        path="/mcp",
    )

if __name__ == "__main__":
    asyncio.run(main())
