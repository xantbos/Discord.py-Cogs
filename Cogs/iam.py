import discord
import asyncio
from discord.ext import commands

class IAM(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.roleList = [] # put strings in here like ["Role1", "Role2"]

    @commands.command(pass_context=True, name="iamnot")
    async def iam_removes_user_role(self, ctx, *, args=""):
        if args == "help":
            await ctx.send(embed=discord.Embed(description="Available Roles to remove: {}\nUsage: f.iamnot <role>".format(", ".join(self.roleList))))
            return
        removeableRoles = self.roleList
        lowerRemoveableRoles = [s.lower() for s in removeableRoles]
        roleNuke = args
        for uRole in ctx.message.author.roles:
            if roleNuke.lower() == uRole.name.lower():
                if roleNuke.lower() in lowerRemoveableRoles:
                    await ctx.message.author.remove_roles(discord.utils.get(ctx.message.author.guild.roles, name=uRole.name))
                    confirmMessage = await ctx.send(embed=discord.Embed(description="{} your role {} has been removed.".format(ctx.message.author.mention,uRole.name)))
                    await asyncio.sleep(5)
                    await confirmMessage.delete()
                    try:
                        await ctx.message.delete()
                    except:
                        pass
                    return
			
    @commands.command(pass_context=True, name="iam")
    async def iam_adds_user_roles(self, ctx, *, args=""):
        if args == "help":
            await ctx.send(embed=discord.Embed(description="Available Roles to add: {}\nUsage: f.iam <role>".format(", ".join(self.roleList))))
            return
        approvedRoles = self.roleList
        targetRole= None
        #await self.bot.send_typing(ctx.message.channel)
        flaggedRole = ""
        for s in approvedRoles:
            if args.lower() == s.lower():
                flaggedRole = s
                break
        targetRole = discord.utils.get(ctx.message.author.guild.roles, name=flaggedRole)
        if not targetRole is None:
            if targetRole.name in approvedRoles:
                await ctx.message.author.add_roles(targetRole)
                confirmMessage = await ctx.send(embed=discord.Embed(description="{} you have been given the role {}".format(ctx.message.author.mention,targetRole.name)))
                await asyncio.sleep(5)
                await confirmMessage.delete()
                try:
                    await ctx.message.delete()
                except:
                    pass
                return
        await ctx.message.delete()
		
def setup(bot):
    bot.add_cog(IAM(bot))