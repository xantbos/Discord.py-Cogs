import discord
from discord.ext import commands


class Owner(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.sessions = set()

    @commands.command(name="setgame")
    async def game_change(self, ctx, *, ngame: str):
        """Lets the bot owner change the game of the bot"""
        await self.bot.change_presence(activity=discord.Game(name=ngame))
        print('Game has now been changed to: {}'.format(ngame))

    @commands.command(name="setavatar")
    async def set_avatar(self, ctx, fileName: str):
        """Lets the bot owner change the avatar of the bot"""
        with open(fileName, 'rb') as image:
            image = image.read()
            await self.bot.user.edit(avatar=image)
            print("My avatar has been changed!")
			
    @commands.command(name="ping")
    async def get_pinged(self, ctx):
        await ctx.send('pong')
		
    @commands.command(name='reload', hidden=True)
    async def reload_a_cog(self, ctx, *, cog: str):
        cogsRoot = "plugins." + cog
        try:
            self.bot.unload_extension(cogsRoot)
            self.bot.load_extension(cogsRoot)
        except Exception as e:
            await ctx.send('Error reloading cog {}: {type(e).__name__} - {}'.format(cog,e))
        else:
            await ctx.send('Cog {} reloaded.'.format(cog))
		
    @commands.command(name="respond", pass_context=True)
    async def responder(self, ctx, channelString, *, message:str=""):
        targetChannel = ctx.message.channel_mentions[0]
        targetMessage = message
        if not targetChannel: return
        await ctx.message.delete()
        await targetChannel.send(targetMessage)
			
    @commands.command(name="logout")
    async def logout(self, ctx):
        em = discord.Embed(title="Logging out...", description="", colour=0x00AE86)
        await ctx.send(embed=em)
        await self.bot.close()
		
    @commands.command(name="servlink")
    async def owner_server_link(self, ctx):
        linkURL = "https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=0".format(self.bot.user.id)
        em = discord.Embed(title="Click here to invite me elsewhere!", description="Discord will tell you links are spoopy. This one isn't.", colour=0x00AE86)
        em.url = linkURL
        await ctx.send(embed=em)
			
def setup(bot):
    bot.add_cog(Owner(bot))
