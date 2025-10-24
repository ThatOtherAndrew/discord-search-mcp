import asyncio
import os
import sys

import discord
import uvicorn
from mcp.server.fastmcp import FastMCP


class DiscordBot:
    def __init__(self):
        self.client: discord.Client | None = None
        self.ready_event = asyncio.Event()

    async def start(self):
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError('DISCORD_TOKEN environment variable not set')

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_ready():
            print(f'Discord bot logged in as {self.client.user}', flush=True)
            self.ready_event.set()

        asyncio.create_task(self.client.start(token))
        await self.ready_event.wait()
        print('Discord client is ready', flush=True)


bot = DiscordBot()
mcp = FastMCP('discord-search-mcp')


@mcp.tool()
def get_guilds() -> str:
    """Get a list of all Discord guilds (servers) the bot is a member of."""
    if not bot.client or not bot.client.is_ready():
        return 'Error: Discord client is not ready. Please ensure the bot is connected.'

    guilds = bot.client.guilds

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


async def startup():
    print('Starting Discord MCP server...', flush=True)
    await bot.start()
    print('Discord MCP server ready!', flush=True)


app = mcp.streamable_http_app()
app.on_event('startup')(startup)


def main():
    if not os.getenv('DISCORD_TOKEN'):
        print('Error: DISCORD_TOKEN environment variable not set', file=sys.stderr)
        sys.exit(1)

    port = int(os.getenv('PORT', 8000))
    print(f'Starting MCP server on http://127.0.0.1:{port}', flush=True)

    uvicorn.run(app, host='127.0.0.1', port=port, log_level='debug')


if __name__ == '__main__':
    main()
