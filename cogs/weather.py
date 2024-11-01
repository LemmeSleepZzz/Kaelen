import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="weather", description="Get the current weather for Tbilisi")
    async def amindi(self, interaction: discord.Interaction):
        url = "https://api.weatherapi.com/v1/current.json"
        params = {
            "key": "d6cb9e09ce09412aa9f140332242310",
            "q": "Tbilisi"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as res:
                time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                data = await res.json()

                location = data["location"]["name"]
                temp_c = data["current"]["temp_c"]
                humidity = data["current"]["humidity"]
                condition = data["current"]["condition"]["text"]
                image_url = "http:" + data["current"]["condition"]["icon"]

                # Create embed message
                embed = discord.Embed(
                    title=f"Weather for `{location}`",
                    description=f"Condition in `{location}` is `{condition}`"
                )
                embed.add_field(name="Temperature", value=f"C : {temp_c}")
                embed.add_field(name="Humidity", value=f"{humidity}")
                embed.set_footer(text=f"{time}")
                embed.set_thumbnail(url=image_url)

                await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
