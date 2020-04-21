import discord
from discord.ext import commands

# Test change

class Misc(commands.Cog): 

    def __init__(self, bot):
        self.bot = bot
							
def setup(bot):
    bot.add_cog(Misc(bot))
