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
def get_guild_info() -> dict:
    """Get a list of all Discord guilds (servers) and the members and channels they contain."""
    client.ensure_ready()

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
    client.ensure_ready()

    route = Route('GET', '/guilds/{guild_id}/messages/search', guild_id=guild_id)
    response = await client.http.request(route, params={
        'content': content,
    })

    return response


@mcp.tool()
async def get_channel_messages(
    channel_id: str,
    message_id: str | None = None,
    direction: str = 'latest',
    limit: int = 50
) -> dict:
    """Get messages from a Discord channel.

    Args:
        channel_id: The channel to fetch messages from
        message_id: Reference message ID (required for 'around', 'before', 'after')
        direction: Where to fetch messages - 'latest', 'around', 'before', or 'after'
        limit: Number of messages to fetch (1-100, default 50)
    """
    client.ensure_ready()

    channel = client.get_channel(int(channel_id))
    if not channel:
        raise ValueError(f'Channel {channel_id} not found')

    limit = max(1, min(100, limit))

    kwargs = {'limit': limit}
    if direction == 'around' and message_id:
        kwargs['around'] = discord.Object(id=int(message_id))
    elif direction == 'before' and message_id:
        kwargs['before'] = discord.Object(id=int(message_id))
    elif direction == 'after' and message_id:
        kwargs['after'] = discord.Object(id=int(message_id))
    elif direction != 'latest':
        raise ValueError(f"direction must be 'latest', 'around', 'before', or 'after'")

    messages = [msg async for msg in channel.history(**kwargs)]

    return {
        'channel_id': channel_id,
        'channel_name': channel.name,
        'message_count': len(messages),
        'messages': [
            {
                'id': str(msg.id),
                'content': msg.content,
                'author': {
                    'id': str(msg.author.id),
                    'name': msg.author.name,
                    'display_name': msg.author.display_name,
                },
                'timestamp': msg.created_at.isoformat(),
                'edited_timestamp': msg.edited_at.isoformat() if msg.edited_at else None,
                'attachments': [
                    {
                        'id': str(att.id),
                        'filename': att.filename,
                        'url': att.url,
                        'content_type': att.content_type,
                    }
                    for att in msg.attachments
                ],
                'embeds': len(msg.embeds),
                'reactions': [
                    {
                        'emoji': str(reaction.emoji),
                        'count': reaction.count,
                    }
                    for reaction in msg.reactions
                ] if msg.reactions else [],
            }
            for msg in messages
        ]
    }


async def run_server(token: str):
    print('Starting Discord MCP server...')
    await client.start(token)

    port = int(os.getenv('PORT', 8000))
    print(f'Starting MCP server on http://127.0.0.1:{port}')

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
