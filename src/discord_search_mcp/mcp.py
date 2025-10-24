from discord.http import Route
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
def get_guilds() -> dict:
    """Get a list of all Discord guilds (servers) the bot is a member of."""
    if not client.is_ready():
        raise RuntimeError('Discord client is not ready. Please ensure the bot is connected.')

    return {'guilds': [
        {
            'id': str(guild.id),
            'name': guild.name,
            'description': guild.description,
            'member_count': guild.member_count,
            'members': [
                {
                    'id': str(member.id),
                    'name': member.name,
                    'global_name': member.global_name,
                    'display_name': member.display_name,
                }
                for member in guild.members
            ],
            'channel_count': len(guild.channels),
            'channels': [
                {
                    'id': str(channel.id),
                    'name': channel.name,
                    'type': str(channel.type),
                    'topic': getattr(channel, 'topic', None),
                }
                for channel in guild.channels
            ],
        }
        for guild in client.guilds
    ]}


@mcp.tool()
async def search_guild(guild_id: str, content: str) -> dict:
    response = await client.http.request(Route(
        'GET',
        '/guilds/{guild_id}/messages/search',
        guild_id=guild_id,
        content=content,
    ))

    return response


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
