import discord
from discord import app_commands
from discord.ext import commands
import sqlite3


database = sqlite3.connect("kaelen.sqlite")
cursor = database.cursor()

cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS settings (
        guild_id INTEGER PRIMARY KEY,
        welcome_channel_id INTEGER,
        welcome_enabled INTEGER DEFAULT 1  -- 1 for enabled, 0 for disabled
    )
""")
database.commit()

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        welcome_channel_id = await self.get_welcome_channel_id(guild_id)
        welcome_enabled = await self.is_welcome_enabled(guild_id)

        if welcome_enabled and welcome_channel_id:
            channel = self.bot.get_channel(welcome_channel_id)
            if channel:
                welcome_message = f"Welcome to the server, {member.mention}! We're glad to have you here!"
                await channel.send(welcome_message)

    async def get_welcome_channel_id(self, guild_id):
        cursor.execute("SELECT welcome_channel_id FROM settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    async def is_welcome_enabled(self, guild_id):
        cursor.execute("SELECT welcome_enabled FROM settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False

    @app_commands.command(name="set_welcome_channel", description="Set the welcome channel for new members.")
    @app_commands.checks.has_permissions(administrator=True) 
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        channel_id = channel.id

        await self.save_welcome_channel_id(guild_id, channel_id)

        await interaction.response.send_message(f"The welcome channel has been set to {channel.mention}.")

    async def save_welcome_channel_id(self, guild_id, channel_id):
        cursor.execute("""
            INSERT OR REPLACE INTO settings (guild_id, welcome_channel_id, welcome_enabled)
            VALUES (?, ?, 1)  -- Default to enabled
        """, (guild_id, channel_id))
        database.commit()

    @app_commands.command(name="enable_welcome", description="Enable the welcome message feature.")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable_welcome(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        cursor.execute("UPDATE settings SET welcome_enabled = 1 WHERE guild_id = ?", (guild_id,))
        database.commit()
        await interaction.response.send_message("Welcome messages have been enabled.")

    @app_commands.command(name="disable_welcome", description="Disable the welcome message feature.")
    @app_commands.checks.has_permissions(administrator=True) 
    async def disable_welcome(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        cursor.execute("UPDATE settings SET welcome_enabled = 0 WHERE guild_id = ?", (guild_id,))
        database.commit()
        await interaction.response.send_message("Welcome messages have been disabled.")

    
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        print(f"Error occurred: {error}")

        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        elif isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message("This command does not exist.", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
