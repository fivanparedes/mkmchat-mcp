"""Entry point for running mkmchat as a module"""

import sys
import asyncio


def main():
    """Main entry point with mode selection"""
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Run HTTP server
        from mkmchat.http_server import run_server, DEFAULT_PORT
        
        port = DEFAULT_PORT
        if len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print(f"Invalid port: {sys.argv[2]}")
                sys.exit(1)
        
        run_server(port)
    else:
        # Run MCP server (default)
        from mkmchat.server import main as mcp_main
        asyncio.run(mcp_main())


if __name__ == "__main__":
    main()
