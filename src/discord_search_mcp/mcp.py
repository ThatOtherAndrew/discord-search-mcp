from discord_search_mcp.client import Client

import asyncio
import os
import sys

import discord
import uvicorn
from mcp.server.fastmcp import FastMCP


client = Client()
mcp = FastMCP('discord-search-mcp')


@mcp.tool()
def get_guilds() -> str:
    """Get a list of all Discord guilds (servers) the bot is a member of."""
    if not client.is_ready():
        return 'Error: Discord client is not ready. Please ensure the bot is connected.'

    guilds = client.guilds

    if not guilds:
        return 'The bot is not a member of any guilds.'

    guild_info = []
    for guild in guilds:
        guild_info.append(
            f'• {guild.name} (ID: {guild.id})\n'
            f'  Members: {guild.member_count}\n'
            f'  Owner: {guild.owner_id}\n'
            f'  Created: {guild.created_at.strftime("%Y-%m-%d")}'
        )

    result = f'Bot is in {len(guilds)} guild(s):\n\n' + '\n\n'.join(guild_info)
    return result


async def run_server(token: str):
    print('Starting Discord MCP server...', flush=True)
    await client.start(token)

    port = int(os.getenv('PORT', 8000))
    print(f'Starting MCP server on http://127.0.0.1:{port}', flush=True)

    config = uvicorn.Config(mcp.streamable_http_app(), host='127.0.0.1', port=port, log_level='debug')
    server = uvicorn.Server(config)
    await server.serve()


def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('Error: DISCORD_TOKEN environment variable not set', file=sys.stderr)
        sys.exit(1)
    else:
        asyncio.run(run_server(token))


if __name__ == '__main__':
    main()
