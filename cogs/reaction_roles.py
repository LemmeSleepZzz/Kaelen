import discord
from discord import app_commands
from discord.ext import commands
import sqlite3


DATABASE_PATH = "kaelen.sqlite"


def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)
def initialize_db():
    with get_db_connection() as db:
        cursor = db.cursor()
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS reaction_roles (
                message_id INTEGER,
                channel_id INTEGER,
                role_id INTEGER,
                emoji TEXT,
                UNIQUE(message_id, channel_id, emoji)  -- Ensure unique entries
            )
        """)
        db.commit()

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        initialize_db()

    @app_commands.command(name="add_reaction_roles", description="Add multiple reaction roles with a description.")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_reaction_roles(self, interaction: discord.Interaction, channel: discord.TextChannel, message_id: str, roles: str, emojis: str, description: str = None):
        print(f"Channel: {channel.name}, Message ID: {message_id}, Roles: {roles}, Emojis: {emojis}, Description: {description}")

        if channel is None:
            await interaction.response.send_message("The specified channel does not exist or is invalid.", ephemeral=True)
            return

        print(f"Using message_id directly: {message_id}")
        role_ids = [int(role.strip()[3:-1]) for role in roles.split(',')] 
        emoji_list = [emoji.strip() for emoji in emojis.split(',')]

        print(f"Role IDs: {role_ids}, Emoji List: {emoji_list}")

        if len(role_ids) != len(emoji_list):
            await interaction.response.send_message("The number of roles and emojis must match.", ephemeral=True)
            return

        try:
            print(f"Attempting to fetch message with ID: {message_id} in channel: {channel.id}")
            message = await channel.fetch_message(int(message_id))
            print(f"Successfully fetched message: {message.content}")

            if description:
                await channel.send(description)
                print(f"Sent description: {description}")

            for role_id, emoji in zip(role_ids, emoji_list):
                with get_db_connection() as db:
                    cursor = db.cursor()
                    cursor.execute(""" 
                        INSERT INTO reaction_roles (message_id, channel_id, role_id, emoji) 
                        VALUES (?, ?, ?, ?) 
                    """, (int(message_id), channel.id, role_id, emoji))
                    db.commit()
                
                print(f"Adding emoji: {emoji} for role ID: {role_id}")
                try:
                    await message.add_reaction(emoji)
                    print(f"Successfully added emoji: {emoji} for role ID: {role_id}")
                except Exception as e:
                    print(f"Failed to add emoji: {emoji} to message ID: {message_id}, Error: {str(e)}")

            await interaction.response.send_message("Reaction roles added! React with the specified emojis.")
        except discord.NotFound:
            await interaction.response.send_message("Message not found. Please check the message ID.", ephemeral=True)
            print(f"Error: Message with ID {message_id} not found in channel {channel.id}.")
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to access that channel or message.", ephemeral=True)
            print(f"Error: Bot does not have permission in the specified channel: {channel.id}.")
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {str(e)}", ephemeral=True)
            print(f"Unexpected error while processing command: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return  

        with get_db_connection() as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT role_id FROM reaction_roles WHERE message_id = ? AND channel_id = ? AND emoji = ?
            """, (payload.message_id, payload.channel_id, str(payload.emoji)))

            result = cursor.fetchone()
            if result:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(result[0])
                member = guild.get_member(payload.user_id)

                if role and member:
                    await member.add_roles(role)
                    print(f"Added role {role.name} to {member.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return  

        with get_db_connection() as db:
            cursor = db.cursor()
            cursor.execute("""
                SELECT role_id FROM reaction_roles WHERE message_id = ? AND channel_id = ? AND emoji = ?
            """, (payload.message_id, payload.channel_id, str(payload.emoji)))

            result = cursor.fetchone()
            if result:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(result[0])
                member = guild.get_member(payload.user_id)

                if role and member:
                    await member.remove_roles(role)
                    print(f"Removed role {role.name} from {member.name}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
