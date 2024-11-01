import discord
from discord import app_commands
from discord.ext import commands
import sqlite3  
import vacefron
import random
import math

database = sqlite3.connect("[Database]")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS levels(user_id INTEGER, guild_id INTEGER, exp INTEGER, level INTEGER, last_lvl INTEGER)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS coins(user_id INTEGER, coin INTEGER)""")

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if message.author.bot:
            return 
        
        cursor.execute("SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id= ? AND guild_id = ?", (message.author.id, message.guild.id))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute("INSERT INTO levels(user_id, guild_id, exp, level, last_lvl) VALUES(?, ?, 0, 0, 0)", (message.author.id, message.guild.id))
            database.commit()
        else:
            exp = result[2]
            last_lvl = result[4]
            
            exp_gained = random.randint(1, 20)
            exp += exp_gained
            lvl = 0.1 * (math.sqrt(exp))

            cursor.execute("UPDATE levels SET exp = ?, level = ? WHERE user_id = ? AND guild_id = ?", (exp, lvl, message.author.id, message.guild.id))
            database.commit()

            if int(lvl) > last_lvl:
                await message.channel.send(f"{message.author.mention} has leveled up to level {int(lvl)}!")
                cursor.execute("UPDATE levels SET last_lvl = ? WHERE user_id = ? AND guild_id = ?", (int(lvl), message.author.id, message.guild.id))
                cursor.execute("SELECT coin FROM coins WHERE user_id = ?", (message.author.id,))
                coin_result = cursor.fetchone()
                
                coins_awarded = 100  
                if coin_result is None:
                    cursor.execute("INSERT INTO coins(user_id, coin) VALUES(?, ?)", (message.author.id, coins_awarded))
                else:
                    current_coins = coin_result[0]
                    new_coins = current_coins + coins_awarded
                    cursor.execute("UPDATE coins SET coin = ? WHERE user_id = ?", (new_coins, message.author.id))
                
                database.commit()

    @app_commands.command(name="level", description="Shows your level or another user's level")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user

        cursor.execute("SELECT exp, level, last_lvl FROM levels WHERE user_id = ? AND guild_id = ?", (user.id, interaction.guild.id))
        user_data = cursor.fetchone()

        if user_data:
            exp, level, last_lvl = user_data
            next_lvl_xp = ((int(level) + 1) / 0.1) ** 2
            next_lvl_xp = int(next_lvl_xp)

            cursor.execute("SELECT COUNT(*) FROM levels WHERE guild_id = ? AND exp > ?", (interaction.guild.id, exp))
            rank = cursor.fetchone()[0] + 1

            rank_card = vacefron.Rankcard(
                username=user.display_name,
                avatar_url=user.avatar.url,
                current_xp=exp,
                next_level_xp=next_lvl_xp,
                previous_level_xp=last_lvl,
                level=int(level),
                rank=rank,
            )
            card_url = await vacefron.Client().rankcard(rank_card)
            embed = discord.Embed(title=f"", color=discord.Color.blue())
            embed.set_image(url=card_url.url)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"{user.mention} does not have any level data.")

        

    @app_commands.command(name="coins", description="Shows you coin")
    async def coin(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user  = interaction.user
        
        cursor.execute("""SELECT coin from coins WHERE user_id = ?""",(user.id,))
        result = cursor.fetchone()
    
        if result:
            coin_balance = result[0]
            await interaction.response.send_message(f"{user.mention} has {coin_balance} coins.")
        else: 
            await interaction.response.send_message(f"{user.mention} has no coins.")

    @app_commands.command(name="transfer", description="Transfer coins to another user")
    async def transfer(self, interaction: discord.Interaction, amount: int, recipient: discord.User):
        if amount <= 0:
            await interaction.response.send_message("You must transfer a positive amount of coins.")
            return

        cursor.execute("SELECT coin FROM coins WHERE user_id = ?", (interaction.user.id,))
        sender_coins = cursor.fetchone()

        if sender_coins is None or sender_coins[0] < amount:
            await interaction.response.send_message("You do not have enough coins to complete this transfer.")
            return

        new_sender_coins = sender_coins[0] - amount
        cursor.execute("UPDATE coins SET coin = ? WHERE user_id = ?", (new_sender_coins, interaction.user.id))

        cursor.execute("SELECT coin FROM coins WHERE user_id = ?", (recipient.id,))
        recipient_coins = cursor.fetchone()

        if recipient_coins is None:
            cursor.execute("INSERT INTO coins(user_id, coin) VALUES(?, ?)", (recipient.id, amount))
        else:
            new_recipient_coins = recipient_coins[0] + amount
            cursor.execute("UPDATE coins SET coin = ? WHERE user_id = ?", (new_recipient_coins, recipient.id))
        database.commit()
        
       
        await interaction.response.send_message(f"You have transferred {amount} coins to {recipient.mention}.")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
