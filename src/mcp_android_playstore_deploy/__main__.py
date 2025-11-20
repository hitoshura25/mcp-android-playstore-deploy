"""Main entry point for the MCP Android Play Store Deploy server."""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server

from . import tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run the MCP server."""
    logger.info("Starting MCP Android Play Store Deploy Server")

    # Create server instance
    server = Server("mcp-android-playstore-deploy")

    # Register all tools
    tools.register_tools(server)

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
