from discord.http import Route
from discord_search_mcp.client import Client

import asyncio
import os
import re
import sys

import discord
import uvicorn
from mcp.server.fastmcp import FastMCP


client = Client()
mcp = FastMCP('discord-search-mcp')


def parse_discord_url(url: str) -> dict | None:
    """Parse a Discord message URL and extract guild_id, channel_id, and message_id.

    Supports formats:
    - https://discord.com/channels/{guild_id}/{channel_id}/{message_id}
    - https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}
    - https://ptb.discord.com/channels/{guild_id}/{channel_id}/{message_id}
    - https://canary.discord.com/channels/{guild_id}/{channel_id}/{message_id}

    Args:
        url: Discord message URL

    Returns:
        dict with guild_id, channel_id, message_id, or None if invalid
    """
    pattern = r'https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/(\d+|@me)/(\d+)/(\d+)'
    match = re.match(pattern, url)
    if match:
        guild_id, channel_id, message_id = match.groups()
        return {
            'guild_id': guild_id if guild_id != '@me' else None,
            'channel_id': channel_id,
            'message_id': message_id,
        }
    return None


@mcp.tool()
async def get_message_from_url(url: str) -> dict:
    """Fetch a Discord message from its URL.

    Args:
        url: Discord message URL (e.g., https://discord.com/channels/123/456/789)

    Returns:
        dict: Message details including content, author, references, and attachments
    """
    parsed = parse_discord_url(url)
    if not parsed:
        raise ValueError(f'Invalid Discord message URL: {url}')

    return await get_message(parsed['channel_id'], parsed['message_id'])


@mcp.tool()
async def get_attachment(channel_id: str, message_id: str, filename: str) -> dict:
    """Get a fresh URL for a Discord attachment.

    Discord attachment URLs expire after 24 hours. This tool re-fetches the message
    to get a fresh, working URL for the attachment.

    Args:
        channel_id: The channel ID containing the message
        message_id: The message ID with the attachment
        filename: The filename of the attachment to fetch

    Returns:
        dict: Attachment metadata with fresh URL, content type, and size
    """
    client.ensure_ready()

    channel = client.get_channel(int(channel_id))
    if not channel:
        raise ValueError(f'Channel {channel_id} not found')

    if not isinstance(channel, discord.abc.Messageable):
        raise ValueError(f'Channel {channel_id} is not a text channel')

    try:
        msg = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        raise ValueError(f'Message {message_id} not found in channel {channel_id}')

    # Find the attachment by filename
    attachment = None
    for att in msg.attachments:
        if att.filename == filename:
            attachment = att
            break

    if not attachment:
        available = [att.filename for att in msg.attachments]
        raise ValueError(f'Attachment "{filename}" not found. Available: {available}')

    return {
        'url': attachment.url,
        'filename': attachment.filename,
        'content_type': attachment.content_type,
        'size': attachment.size,
        'width': attachment.width if hasattr(attachment, 'width') else None,
        'height': attachment.height if hasattr(attachment, 'height') else None,
        'note': 'This is a fresh URL that should work for the next 24 hours. Use it directly to view/download.',
    }


@mcp.tool()
def get_guild_info(include_members: bool = False, include_channels: bool = True) -> dict:
    """Get a list of all Discord guilds (servers).

    Args:
        include_members: Include member list (expensive, default False)
        include_channels: Include channel list (default True)

    Returns:
        dict: List of guilds with requested details
    """
    client.ensure_ready()

    guilds = []
    for guild in client.guilds:
        guild_data = {
            'id': str(guild.id),
            'name': guild.name,
            'description': guild.description,
            'member_count': guild.member_count,
            'channel_count': len(guild.channels),
        }

        if include_channels:
            guild_data['channels'] = [
                {
                    'id': str(channel.id),
                    'name': channel.name,
                    'type': str(channel.type),
                }
                for channel in guild.channels
                if hasattr(channel, 'name')
            ]

        if include_members:
            guild_data['members'] = [
                {
                    'id': str(member.id),
                    'name': member.name,
                    'display_name': member.display_name,
                }
                for member in guild.members
            ]

        guilds.append(guild_data)

    return {'guilds': guilds}


@mcp.tool()
async def get_active_threads(guild_id: str, limit: int = 10) -> dict:
    """Get active threads in a guild.

    Args:
        guild_id: The guild to fetch active threads from
        limit: Maximum number of threads to return (1-100, default 10)

    Returns:
        dict: List of active threads with essential details
    """
    client.ensure_ready()

    limit = max(1, min(100, limit))

    route = Route('GET', '/guilds/{guild_id}/threads/active', guild_id=guild_id)
    response = await client.http.request(route)

    threads = response.get('threads', [])
    total_count = len(threads)

    # Sort by message_count descending to get most active threads first
    threads_sorted = sorted(threads, key=lambda t: t.get('message_count', 0), reverse=True)
    threads_limited = threads_sorted[:limit]

    return {
        'guild_id': guild_id,
        'total_active_threads': total_count,
        'returned_count': len(threads_limited),
        'note': f'Showing {len(threads_limited)} of {total_count} active threads (sorted by activity). Increase limit parameter to see more.',
        'threads': [
            {
                'id': str(thread['id']),
                'name': thread.get('name'),
                'parent_channel_id': str(thread.get('parent_id')),
                'message_count': thread.get('message_count', 0),
                'member_count': thread.get('member_count', 0),
            }
            for thread in threads_limited
        ]
    }


@mcp.tool()
async def get_archived_threads(channel_id: str, public: bool = True, limit: int = 10) -> dict:
    """Get archived threads from a channel.

    Args:
        channel_id: The channel to fetch archived threads from
        public: Whether to fetch public (True) or private (False) archived threads
        limit: Number of threads to fetch (2-100, default 10)

    Returns:
        dict: List of archived threads with essential details
    """
    client.ensure_ready()

    limit = max(2, min(100, limit))
    thread_type = 'public' if public else 'private'

    route = Route('GET', f'/channels/{{channel_id}}/threads/archived/{thread_type}', channel_id=channel_id)
    response = await client.http.request(route, params={'limit': limit})

    threads = response.get('threads', [])
    has_more = response.get('has_more', False)

    return {
        'channel_id': channel_id,
        'thread_type': thread_type,
        'thread_count': len(threads),
        'has_more': has_more,
        'threads': [
            {
                'id': str(thread['id']),
                'name': thread.get('name'),
                'parent_channel_id': str(thread.get('parent_id')),
                'message_count': thread.get('message_count', 0),
                'member_count': thread.get('member_count', 0),
                'archive_timestamp': thread.get('thread_metadata', {}).get('archive_timestamp'),
                'locked': thread.get('thread_metadata', {}).get('locked', False),
            }
            for thread in threads
        ]
    }


@mcp.tool()
async def search_guild(guild_id: str, content: str, limit: int = 10) -> dict:
    """Search for messages in a guild.

    Args:
        guild_id: The guild to search in
        content: Text to search for
        limit: Maximum results to return (1-25, default 10)

    Returns:
        dict: Search results with message summaries
    """
    client.ensure_ready()

    limit = max(1, min(25, limit))

    route = Route('GET', '/guilds/{guild_id}/messages/search', guild_id=guild_id)
    response = await client.http.request(route, params={
        'content': content,
        'limit': limit,
    })

    # Simplify response structure
    messages = response.get('messages', [])
    total_results = response.get('total_results', 0)

    return {
        'total_results': total_results,
        'message_count': len(messages),
        'messages': [
            {
                'id': str(msg[0]['id']),
                'channel_id': str(msg[0]['channel_id']),
                'content': msg[0]['content'][:200] + '...' if len(msg[0]['content']) > 200 else msg[0]['content'],
                'author': {
                    'id': str(msg[0]['author']['id']),
                    'username': msg[0]['author'].get('username', 'Unknown'),
                },
                'timestamp': msg[0]['timestamp'],
            }
            for msg in messages
            if msg and len(msg) > 0
        ]
    }


@mcp.tool()
async def get_message(channel_id: str, message_id: str) -> dict:
    """Fetch a specific message by channel and message ID.

    Args:
        channel_id: The channel ID containing the message
        message_id: The message ID to fetch

    Returns:
        dict: Message details including content, author, references, embeds, attachments, and threads
    """
    client.ensure_ready()

    channel = client.get_channel(int(channel_id))
    if not channel:
        raise ValueError(f'Channel {channel_id} not found')

    if not isinstance(channel, discord.abc.Messageable):
        raise ValueError(f'Channel {channel_id} is not a text channel')

    try:
        msg = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        raise ValueError(f'Message {message_id} not found in channel {channel_id}')

    result = {
        'id': str(msg.id),
        'channel_id': str(msg.channel.id),
        'content': msg.content,
        'author': {
            'id': str(msg.author.id),
            'name': msg.author.name,
            'display_name': msg.author.display_name,
        },
        'timestamp': msg.created_at.isoformat(),
        'edited_timestamp': msg.edited_at.isoformat() if msg.edited_at else None,
        'jump_url': msg.jump_url,
    }

    # Reply information (always included with preview)
    if msg.reference:
        result['reply_to'] = {
            'message_id': str(msg.reference.message_id),
            'channel_id': str(msg.reference.channel_id),
            'guild_id': str(msg.reference.guild_id) if msg.reference.guild_id else None,
        }

        # Include preview of referenced message
        if msg.reference.resolved and isinstance(msg.reference.resolved, discord.Message):
            result['reply_to']['content_preview'] = msg.reference.resolved.content[:200] + '...' if len(msg.reference.resolved.content) > 200 else msg.reference.resolved.content
            result['reply_to']['author'] = msg.reference.resolved.author.display_name
            result['reply_to']['jump_url'] = msg.reference.resolved.jump_url

    # Thread information
    if hasattr(msg, 'thread') and msg.thread:
        result['thread'] = {
            'id': str(msg.thread.id),
            'name': msg.thread.name,
            'message_count': msg.thread.message_count,
            'member_count': msg.thread.member_count if hasattr(msg.thread, 'member_count') else None,
            'archived': msg.thread.archived if hasattr(msg.thread, 'archived') else None,
        }

    # Forwarded messages (message snapshots)
    # Note: MessageSnapshot structure varies, safely extract available data
    if hasattr(msg, 'message_snapshots') and msg.message_snapshots:
        forwarded = []
        for snapshot in msg.message_snapshots:
            snap_data = {}
            if hasattr(snapshot, 'content'):
                content = snapshot.content
                snap_data['content'] = content[:200] + '...' if len(content) > 200 else content
            if hasattr(snapshot, 'author'):
                snap_data['author'] = getattr(snapshot.author, 'display_name', 'Unknown')
            if hasattr(snapshot, 'timestamp') and callable(getattr(snapshot.timestamp, 'isoformat', None)):
                snap_data['timestamp'] = snapshot.timestamp.isoformat()  # type: ignore[misc]
            if hasattr(snapshot, 'guild_id'):
                snap_data['guild_id'] = str(snapshot.guild_id) if snapshot.guild_id else None
            if hasattr(snapshot, 'channel_id'):
                snap_data['channel_id'] = str(snapshot.channel_id) if snapshot.channel_id else None

            if snap_data:  # Only add if we found some data
                forwarded.append(snap_data)

        if forwarded:
            result['forwarded_messages'] = forwarded

    # Attachments (metadata only, no content)
    if msg.attachments:
        result['attachments'] = [
            {
                'id': str(att.id),
                'filename': att.filename,
                'url': att.url,
                'content_type': att.content_type,
                'size': att.size,
            }
            for att in msg.attachments
        ]

    # Embeds (with content)
    if msg.embeds:
        result['embeds'] = [
            {
                'type': embed.type,
                'title': embed.title,
                'description': (embed.description[:300] + '...' if embed.description and len(embed.description) > 300 else embed.description) if embed.description else None,
                'url': embed.url,
                'image': embed.image.url if embed.image else None,
                'thumbnail': embed.thumbnail.url if embed.thumbnail else None,
                'author': embed.author.name if embed.author else None,
                'footer': embed.footer.text if embed.footer else None,
            }
            for embed in msg.embeds
        ]

    # Reactions (summary)
    if msg.reactions:
        result['reactions'] = [
            {
                'emoji': str(reaction.emoji),
                'count': reaction.count,
            }
            for reaction in msg.reactions
        ]

    return result


@mcp.tool()
async def get_channel_messages(
    channel_id: str,
    message_id: str | None = None,
    direction: str = 'latest',
    limit: int = 25
) -> dict:
    """Get messages from a Discord channel.

    Args:
        channel_id: The channel to fetch messages from
        message_id: Reference message ID (required for 'around', 'before', 'after')
        direction: Where to fetch messages - 'latest', 'around', 'before', or 'after'
        limit: Number of messages to fetch (1-100, default 25)

    Returns:
        dict: Channel info and message summaries
    """
    client.ensure_ready()

    channel = client.get_channel(int(channel_id))
    if not channel:
        raise ValueError(f'Channel {channel_id} not found')

    if not isinstance(channel, discord.abc.Messageable):
        raise ValueError(f'Channel {channel_id} is not a text channel')

    limit = max(1, min(100, limit))

    if direction == 'around' and message_id:
        messages = [msg async for msg in channel.history(limit=limit, around=discord.Object(id=int(message_id)))]
    elif direction == 'before' and message_id:
        messages = [msg async for msg in channel.history(limit=limit, before=discord.Object(id=int(message_id)))]
    elif direction == 'after' and message_id:
        messages = [msg async for msg in channel.history(limit=limit, after=discord.Object(id=int(message_id)))]
    elif direction == 'latest':
        messages = [msg async for msg in channel.history(limit=limit)]
    else:
        raise ValueError(f"direction must be 'latest', 'around', 'before', or 'after'")

    channel_name = getattr(channel, 'name', str(channel_id))

    return {
        'channel_id': channel_id,
        'channel_name': channel_name,
        'message_count': len(messages),
        'messages': [
            {
                'id': str(msg.id),
                'content': msg.content[:300] + '...' if len(msg.content) > 300 else msg.content,
                'author': {
                    'id': str(msg.author.id),
                    'display_name': msg.author.display_name,
                },
                'timestamp': msg.created_at.isoformat(),
                'jump_url': msg.jump_url,

                # Reply information (always included)
                'reply_to': {
                    'message_id': str(msg.reference.message_id),
                    'channel_id': str(msg.reference.channel_id),
                    'content_preview': msg.reference.resolved.content[:100] + '...' if msg.reference.resolved and isinstance(msg.reference.resolved, discord.Message) and len(msg.reference.resolved.content) > 100 else (msg.reference.resolved.content if msg.reference.resolved and isinstance(msg.reference.resolved, discord.Message) else None),
                    'author': msg.reference.resolved.author.display_name if msg.reference.resolved and isinstance(msg.reference.resolved, discord.Message) else None,
                } if msg.reference else None,

                # Thread information
                'thread': {
                    'id': str(msg.thread.id),
                    'name': msg.thread.name,
                    'message_count': msg.thread.message_count,
                    'member_count': msg.thread.member_count if hasattr(msg.thread, 'member_count') else None,
                } if hasattr(msg, 'thread') and msg.thread else None,

                # Forwarded messages (message snapshots) - Note: May not be available in all discord.py versions
                'forwarded_count': len(getattr(msg, 'message_snapshots', [])),

                # Embeds (always included with content)
                'embeds': [
                    {
                        'type': embed.type,
                        'title': embed.title,
                        'description': (embed.description[:200] + '...' if embed.description and len(embed.description) > 200 else embed.description) if embed.description else None,
                        'url': embed.url,
                        'image': embed.image.url if embed.image else None,
                        'thumbnail': embed.thumbnail.url if embed.thumbnail else None,
                    }
                    for embed in msg.embeds
                ] if msg.embeds else [],

                # Attachment metadata
                'attachments': [
                    {
                        'filename': att.filename,
                        'url': att.url,
                        'content_type': att.content_type,
                        'size': att.size,
                    }
                    for att in msg.attachments
                ] if msg.attachments else [],

                'reaction_count': len(msg.reactions) if msg.reactions else 0,
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
