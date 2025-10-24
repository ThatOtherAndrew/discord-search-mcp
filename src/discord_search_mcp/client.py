import asyncio

import discord

class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)

        self.ready_event = asyncio.Event()

    async def start(self, token: str):
        asyncio.create_task(super().start(token))
        await self.ready_event.wait()

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        self.ready_event.set()

    def ensure_ready(self):
        if not self.is_ready():
            raise RuntimeError('Discord client is not ready. Please wait 5 seconds and try again.')
