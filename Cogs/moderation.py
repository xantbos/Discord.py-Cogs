import discord
from discord.ext import commands
import json
import re

from pathlib import Path

#entire import block is for timed mute function
from datetime import date, datetime, timedelta, timezone
from threading import Timer
from pytz import timezone
import pytz
import asyncio

localland = timezone("Canada/Eastern")
timeFormat = "%Y-%m-%d-%H-%M-%S"

logChannel = "activitylog"

# Larger class designed as a mod toolbox.
# Supports Muting and Unmuting
# Supports Kicking and Banning
# Supports Striking and Warning

class Moderation(commands.Cog):
	
    def __init__(self, bot):
        self.bot = bot
        self.filerepo = "" # path terminating in / or \ to desired file location
        asyncio.ensure_future(self.MuteLauncher())
		
    async def MuteLauncher(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.mod_bot_timer_for_mute_checks()
            except Exception as e:
                print("Mute crash: {}".format(e))
        print("Terminating Mute")
		
    @commands.command(name='moddebug')
    async def mod_bot_debugs_things(self, ctx):
        pass
		
    @commands.command(name="purge")
    async def mod_purge(self, ctx, limit: int):
        try:
            await ctx.message.channel.purge(limit=limit, before=ctx.message)
            await ctx.send(embed=discord.Embed(description="{0} messages deleted.".format(limit)))
            await ctx.message.delete()
        except discord.errors.Forbidden:
            await ctx.send("Sorry, I don't have the `manage messages` permission")
			
    @commands.command(name="warn")
    async def mod_warn_member(self, ctx, userMention, *, reason=""):
        trimmedMention = bot_logic_for_getting_id(userMention)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = ctx.message.guild.get_member(int(trimmedMention))
        warningBody = "{0} has been warned.".format(targetUser)
        warningReason = ""
        if not reason == "":
            warningReason += "\nReason: {}".format(reason)
        else:
            warningReason = "No reason given."
        em = discord.Embed(title=warningBody, description=warningReason, colour=0x00AE86)
        await ctx.send(embed=em)
        em = discord.Embed(title="You have been warned by {} in the {} server".format(ctx.message.author.name, ctx.message.guild.name), description=warningReason, colour=0x00AE86)
        em.set_footer(text="This is a warning, not a strike. Even so, you better take it seriously.")
        try:
            await targetUser.send(embed=em)
            await self.write_modaction_to_logchannel("Warn", ctx.message.author, targetUser, reason)
            await ctx.message.delete()
        except:
            pass	
			
    @commands.command(name="strikelog")
    async def mod_show_member_strike_logs(self, ctx, target):
        trimmedMention = bot_logic_for_getting_id(target)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = ctx.message.guild.get_member(int(trimmedMention))
        strikeLog = returnJson(self.filerepo, "strikelog")
        serverID = str(ctx.message.guild.id)
        if str(targetUser.id) in strikeLog[serverID]:
            targetUserLog = strikeLog[serverID][str(targetUser.id)]
        else:
            if targetUser:
                await ctx.send("{} currently has no strikes.".format(targetUser.name))
            else:
                await ctx.send("The user in question currently has no strikes.")
            await ctx.message.delete()
            return
        strikeCount = targetUserLog['count']
        if targetUser:
            em = discord.Embed(title="Strike Log for {}".format(targetUser.name), description="Below is a list of all strikes logged.", colour=0x00AE86)
        else:
            em = discord.Embed(title="Strike Log for {}".format(targetID), description="Below is a list of all strikes logged.", colour=0x00AE86)
        for x in range(1,strikeCount+1):
            if 'strike'+str(x) in targetUserLog:
                resolvedMod = ctx.message.guild.get_member(int(targetUserLog["strikeu" + str(x)]))
                if resolvedMod:
                    em.add_field(name="Strike #" + str(x), value="**Moderator:** {}\n**Reason:** {}".format(resolvedMod.name, targetUserLog["strike" + str(x)]), inline=False)
                else:
                    em.add_field(name="Strike #" + str(x), value="**Moderator:** {} (Could not find the user)\n**Reason:** {}".format(targetUserLog["strikeu" + str(x)], targetUserLog["strike" + str(x)]), inline=False)
            else:
                em.add_field(name="Strike #" + str(x), value="Strike issued before logging was enabled, sorry </3")
        em.set_footer(text="I did a thing.")
        await ctx.send(embed=em)
        await ctx.message.delete()
			
    @commands.command(name="strike")
    async def mod_strikes_member(self, ctx, userMention, *, reason=""):
        #if reason == "test" and ctx.message.author.id == int(self.bot.ownerid):
            #await ctx.send("`{}`".format(userMention))
        trimmedMention = bot_logic_for_getting_id(userMention)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = None
        try:
            targetUser = ctx.message.guild.get_member(int(trimmedMention))
        except:
            await ctx.send("There was an error getting the user.")
            return
        if targetUser is None:
            await ctx.send("You linked an invalid number or user.")
            return
        warningBody = "{0} has been given a strike.".format(targetUser)
        warningReason = ""
        if not reason == "":
            warningReason += "\nReason: {}".format(reason)
        else:
            warningReason = "No reason given."
        strikeLog = returnJson(self.filerepo, "strikelog")
        serverID = str(ctx.message.guild.id)
        strikeLog = create_user_key(strikeLog, serverID, str(targetUser.id))
        strikeCount = strikeLog[serverID][str(targetUser.id)]['count']
        strikeLog[serverID][str(targetUser.id)]["strike" + str(strikeCount)] = warningReason[9:]
        strikeLog[serverID][str(targetUser.id)]["strikeu" + str(strikeCount)] = str(ctx.message.author.id)
        setJson(self.filerepo, "strikelog", strikeLog)
        if strikeCount >= 3: warningReason += "\n\n**This is your third strike and you are banned.**"
        em = discord.Embed(title=warningBody, description=warningReason, colour=0x00AE86)
        await ctx.message.channel.send(embed=em)
        em = discord.Embed(title="You have been given a strike by {} in the {} server".format(ctx.message.author.name, ctx.message.guild.name), description=warningReason, colour=0x00AE86)
        if strikeCount < 3:
            em.set_footer(text="This is a strike. You are currently sitting at {} strikes in this server.".format(strikeCount))
        else:
            em.set_footer(text="If you feel your ban is unjustified, please contact an admin of the server.")
        try:
            await targetUser.send(embed=em)
            await self.write_modaction_to_logchannel("Strike", ctx.message.author, targetUser, reason)
            await ctx.message.delete()
            if strikeCount >= 3: await targetUser.ban()
        except:
            pass

    @commands.command(name="ban")
    async def mod_ban_member(self, ctx, target, *, reason=""):
        #if reason == "test" and ctx.message.author.id == int(self.bot.ownerid):
            #await ctx.send("`{}`".format(userMention))
        trimmedMention = bot_logic_for_getting_id(target)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = ctx.message.guild.get_member(int(trimmedMention))
        try:
            banPersonalHeader = "You have been banned from the {} server by {}.".format(ctx.message.guild.name, ctx.message.author.name)
            banBody = "{} has been banned.".format(targetUser)
            banReason = ""
            if not reason == "":
                banReason += "\nReason: {}".format(reason)
            else:
                banReason = "No reason given."
            em = discord.Embed(title=banBody, description=banReason, colour=0x00AE86)
            await ctx.send(embed=em)
            em = discord.Embed(title=banPersonalHeader, description=banReason, colour=0x00AE86)
            await targetUser.send(embed=em)
            await targetUser.ban(reason=reason)
            await self.write_modaction_to_logchannel("Ban", ctx.message.author, targetUser, reason)
        except discord.errors.Forbidden:
            await ctx.send("Sorry, your target is either higher on the food chain or I am missing the `ban` permission.")
        except discord.errors.HTTPException:
            await ctx.send("Sorry, I am a useless bot. Ban failed.")
        await ctx.message.delete()
			
    @commands.command(name="mute")
    async def mod_mute_member(self, ctx, target, time, *, reason=""):
        #if reason == "test" and ctx.message.author.id == int(self.bot.ownerid):
            #await ctx.send("`{}`".format(userMention))
        trimmedMention = bot_logic_for_getting_id(target)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = ctx.message.guild.get_member(int(trimmedMention))
        thisRoleName = "Muted"
        if reason=="": reason="<None was given.>"
        targetRole = None
        targetRole = discord.utils.get(targetUser.guild.roles, name=thisRoleName)
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
        try:
            if targetRole:
                await targetUser.add_roles(targetRole)
                overwrite = bot_generate_overwrite_object(False)
                for channel in ctx.message.guild.channels:
                    await channel.set_permissions(targetUser, overwrite=overwrite)
                em = discord.Embed(title="Mute Issued", description="Moderator {} has applied a mute to {}".format(ctx.message.author.name, targetUser.name), colour=0x00AE86)
                em.add_field(name="Reason", value=reason)
            else:
                outMessage = "The role `{}` was unavailable to apply.".format(thisRoleName)
                em = discord.Embed(title="Error Encountered", description=outMessage, colour=0x00AE86)
        except:
            em = discord.Embed(title="Error Encountered", description="Unknown error raised.", colour=0x00AE86)
        timeToMute = int(time)
        data = returnJson(self.filerepo, "timedmutes")
        try:
            #assume user exists, check if mute is active
			#if not perma mute
            if not data[targetUser.id]["endtime"] == "":
			    #check if it's a perma mute now
                if timeToMute == 0:
                    #perma mute
                    data[targetUser.id]["endtime"] = ""
                    data[targetUser.id]["server"] = ctx.message.guild.id
                    pass
                #it isn't, continue as normal
            elif data[targetUser.id]["endtime"] == "0":
                pass
            else:
			    #perma mute was set up, throw message
                await ctx.send("User {} has already been hit with a permamute.".format(targetUser.name))
                return
        except:
            #user is new to punishment, inject their keys
            newUser = {
                'endtime' : "",
				'server' : ctx.message.guild.id,
                'reply' : 'mc'
            }
            data[targetUser.id] = newUser
        #apply mute timer
        if timeToMute == 0:
            em.add_field(name="Duration", value="Permanent", inline=False)
            em.set_footer(text="You done goofed, boi")
            data[targetUser.id]["server"] = ctx.message.guild.id
        else:
            em.add_field(name="Duration", value="{} minute(s).".format(time), inline=False)
            rightNow = localland.localize(datetime.now())
            newTime = rightNow + timedelta(minutes=timeToMute)
            data[targetUser.id]["endtime"] = newTime.strftime(timeFormat)
            data[targetUser.id]["server"] = ctx.message.guild.id
            setJson(self.filerepo, "timedmutes", data)
        await ctx.message.delete()
        await ctx.send(embed=em)	
        em.add_field(name="Server", value="{} Server".format(ctx.message.guild.name))
        await targetUser.send(embed=em)
        await self.write_modaction_to_logchannel("Mute", ctx.message.author, targetUser, reason)
		
    @commands.command(name="unmute")
    async def mod_unmute_member(self, ctx, target):
        #if reason == "test" and ctx.message.author.id == int(self.bot.ownerid):
            #await ctx.send("`{}`".format(userMention))
        trimmedMention = bot_logic_for_getting_id(target)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = ctx.message.guild.get_member(int(trimmedMention))
        errorMsg = ""
        targetServer = ctx.message.guild
        thisRoleName = "Muted"
        targetRole = discord.utils.get(targetUser.guild.roles, name=thisRoleName)
        try:
            if targetRole:
                errorMsg = "Error on remove_roles (unmute)"
                await targetUser.remove_roles(targetRole)
                errorMsg = "Error in channel_loop (unmute)"
                for channel in ctx.message.guild.channels:
                    await channel.set_permissions(targetUser, overwrite=None)
                em = discord.Embed(title="Mute Lifted", description="Moderator {} has removed mute from {}".format(ctx.message.author.name, targetUser.name), colour=0x00AE86)
                errorMsg = "Error in messaging user (unmute)"
                await targetUser.send("Your mute in {} has been removed.".format(targetServer.name))
            else:
                outMessage = "The role `{}` could not be found.".format(thisRoleName)
                em = discord.Embed(title="Error Encountered", description=outMessage, colour=0x00AE86)
        except:
            em = discord.Embed(title="Error Encountered", description=errorMsg, colour=0x00AE86)
        data = returnJson(self.filerepo, "timedmutes")
        del data[str(targetUser.id)]
        setJson(self.filerepo, "timedmutes", data)
        await ctx.send(embed=em)
        await self.write_modaction_to_logchannel("Unmute", ctx.message.author, targetUser, "")
		
    @commands.command(name="kick")
    async def mod_kick_member(self, ctx, target, *, reason=""):
        trimmedMention = bot_logic_for_getting_id(target)
        if not trimmedMention:
            await ctx.send("You forgot to mention a valid user or their id.")
            return
        targetUser = ctx.message.guild.get_member(int(trimmedMention))
        try:
            await targetUser.kick()
            await ctx.send("```{0} has been kicked for {1}```".format(targetUser, reason))
            await self.write_modaction_to_logchannel("Kick", ctx.message.author, targetUser, reason)
        except discord.errors.Forbidden:
            await ctx.send("Sorry, your target is either higher on the food chain or I am missing the `kick` permission.")
        except discord.errors.HTTPException:
            await ctx.send("Sorry, I am a useless bot. Kick failed.")
        await ctx.message.delete()
							
    async def mod_bot_timer_for_mute_checks(self):
        await self.bot.wait_until_ready()
        preString = "Starting Mute Timer..."
        print("{:<35}".format(preString), end="")
        print("\tSuccess")
        doNothing = True
        while doNothing:
            markedForDeletion = []
            data = returnJson(self.filerepo, "timedmutes")
            for i in data:
                targetToUnmute = None
                if not i.lower() == "control" and not data[i]["endtime"]=="" and not data[i]["endtime"] == "0" and data[i]['reply'] == 'mc':
                    if (localland.localize(datetime.strptime(data[i]["endtime"], timeFormat)) - localland.localize(datetime.now())).total_seconds() < 0:
                        targetServer = self.bot.get_guild(data[i]["server"])
                        targetToUnmute = targetServer.get_member(int(i))
                        targetRole = discord.utils.get(targetServer.roles, name="Muted")
                        if targetToUnmute:
                            for channel in targetServer.channels:
                                await channel.set_permissions(targetToUnmute, overwrite=None)
                            try:
                                await targetToUnmute.send("Your mute in {} has been removed.".format(targetServer.name))
                            except:
                                pass
                        else:
                            #assume user has been deleted
                            pass
	    				#purge entry to speed startup time
                        markedForDeletion.append(i)
                        if targetToUnmute and targetRole:
                            await targetToUnmute.remove_roles(targetRole)
                targetToUnmute = None
            for i in markedForDeletion:
                del data[i]
            markedForDeletion = []
            setJson(self.filerepo, "timedmutes", data)
            data = None
            await asyncio.sleep(5)
	
    async def write_modaction_to_logchannel(self, type, caster, target, reason):	
        if not caster.guild:
            return
        headerImg = ":exclamation:"
        thisChannel = discord.utils.get(caster.guild.channels, name=logChannel)
	
        est = timezone("Canada/Eastern")
        utc = timezone("UTC")
        est_dt = est.localize(datetime.now())

        em = discord.Embed(title="{}Moderation Action [{}]".format(headerImg, type), description="Invoker: {}\nTarget: {}".format(caster.name, target.name), colour=0x00AE86)
        if not type == "Unmute": em.add_field(name="Reason", value=reason, inline=False)
        em.set_footer(text=est_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
        try:
            await thisChannel.send(embed=em)
        except:
            pass

def bot_logic_for_getting_id(userMention):
    pattern = re.compile("^[<][@][0-9]+[>]$")
    patternNick = re.compile("^[<][@][!][0-9]+[>]$")
    trimmedMention = ""
    if userMention.isdigit():
        trimmedMention = userMention
    elif pattern.match(userMention):
        swap = re.compile("[<@>]")
        trimmedMention = swap.sub("", userMention)
    elif patternNick.match(userMention):
        swap = re.compile("[<@!>]")
        trimmedMention = swap.sub("", userMention)
    else:
        trimmedMention = None
    return trimmedMention
	
# due to discord role hierarchy being very clunky
# we apply mute at a channel permission level for the user in question
# this bypasses all roles, except ones that have admin obviously	
def bot_generate_overwrite_object(value):
    overwrite = discord.PermissionOverwrite()
	#overwrite.read_messages = value
    overwrite.send_messages = value
    overwrite.send_tts_messages = value
    overwrite.embed_links = value
    overwrite.attach_files = value
    overwrite.add_reactions = value
    return overwrite
		
def create_user_key(data, serverID, userID):
    if not serverID in data:
        newServer = { userID : { "count" : 0,},}
        data[serverID] = newServer 
        data[serverID][userID]["count"] = 1		
    else:
        if userID in data[serverID]:
            strikecount = data[serverID][userID]["count"]
            data[serverID][userID]["count"] = strikecount + 1
        else:
            newUser = { "count": 0 }
            data[serverID][userID] = newUser
            data[serverID][userID]["count"] = 1
    return data
		
def returnJson(filePath, fileName):
    if fileName.endswith('.json'):
        fileName = fileName[:-5]
    with open(filePath + fileName + '.json') as data_file:    
        data = json.load(data_file)
    return data
	
def setJson(filePath, fileName, data):
    if fileName.endswith('.json'):
        fileName = fileName[:-5]
    copyfile(filePath + fileName + '.json', filePath + fileName + '.json.archive')
    with open(filePath + fileName + '.json', 'w') as outfile:
        json.dump(data, outfile, indent=2)
							
def setup(bot):
    bot.add_cog(Moderation(bot))
