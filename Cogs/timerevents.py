import discord
import asyncio
import pytz
import io
import os
import sys
from discord.ext import commands
from datetime import date, datetime, timedelta, timezone
from threading import Timer
from pytz import timezone

localland = timezone("Canada/Eastern")

class TimerCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ticker = localland.localize(datetime(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, hour=12, minute=00, second=00))
        asyncio.ensure_future(timer_loop(self))		
		
    @commands.command(name="timercheck")
    async def timer_print_internal_times(self, ctx):
        print("TIMER: {}".format(self.ticker.strftime("%B")))

async def timer_loop(self):
    await self.bot.wait_until_ready()
    preString = "Starting Ticker Timer..."
    print("{:<35}".format(preString), end="")
    print("\tSuccess") # purely for aesthetics
    while True:
        diff = self.ticker - localland.localize(datetime.now())
        if diff.total_seconds() <= 0:
			# here is where we increment to our next timer event
			# read up on timedelta if you need help
            self.ticker = self.ticker + timedelta(days=1)
        else:			
            diff = self.ticker - localland.localize(datetime.now())
            await asyncio.sleep(diff.total_seconds())
            thisChannel = self.bot.get_channel(000000000000) # channel id goes here
            await thisChannel.send("Timer tick")
		
def setup(bot):
    bot.add_cog(TimerCommands(bot))