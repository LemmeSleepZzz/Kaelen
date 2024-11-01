import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import sys
import os
import aiohttp

# Load environment variables
load_dotenv(".env")
TOKEN = os.getenv("TOKEN")

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class ds_client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)

    async def on_ready(self):
        print(f"{self.user} Says Hi")
        await self.sync_commands()
        await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name="Thrall"))

    async def sync_commands(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(f"Error during syncing {e}")

client = ds_client()

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with client:
        await load()
        await client.start(TOKEN)

asyncio.run(main())
