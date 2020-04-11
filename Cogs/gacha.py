import discord
import ctypes
import asyncio
from discord.ext import commands
from discord.ext.commands import BucketType
import random
import json
import os
import os.path
import datetime
import math
import pytz
from pytz import timezone
from PIL import Image, ImageDraw, ImageFont
from datetime import date, datetime, timedelta, timezone
from utils.filemg import returnJson, returnJsonUnicode
from collections import Counter
from utils.checks import is_owner
from utils.filemg import (
returnJson, returnJsonUnicode, 
getSimuGachaData, setSimuGachaData
)

massTestFlag = False
massTestValue = 10000

noImageFlag = False

requiresSQFlag = False

class RollResult():

	def __init__(self,ssrS,ssrC,srS,srC,rS,rC,
				servants,ce,cost,summary):
		self.ssrServantRolled=ssrS
		self.srServantRolled=srS
		self.rServantRolled=rS
		self.ssrCERolled=ssrC
		self.srCERolled=srC
		self.rCERolled=rC
		self.servantRolled=servants
		self.ceRolled=ce
		self.sqcost=cost
		self.imagePath=None
		self.rollSummary = summary
		
	def __add__(self,roll):
		ssrS = self.ssrServantRolled + roll.ssrServantRolled
		srS = self.srServantRolled + roll.srServantRolled
		rS = self.rServantRolled + roll.rServantRolled
		ssrC = self.ssrCERolled + roll.ssrCERolled
		srC = self.srCERolled + roll.srCERolled
		rC = self.rCERolled + roll.rCERolled
		servants = self.servantRolled + roll.servantRolled
		ce = self.ceRolled + roll.ceRolled
		cost = self.sqcost + roll.sqcost
		summary = self.rollSummary + roll.rollSummary
		return RollResult(ssrS,ssrC,srS,srC,rS,rC,servants,ce,cost,summary)
		
	def __str__(self):
		return "SSRS: {}\nSRS: {}\nRS: {}\nSSRCE: {}\nSRCE: {}\nRCE: {}\nSERVANTS: {}\nCE: {}\nSUMMARY: {}\n".format(
		self.ssrServantRolled,self.srServantRolled,self.rServantRolled,
		self.ssrCERolled,self.srCERolled,self.rCERolled,
		self.servantRolled,self.ceRolled,self.rollSummary
		)

class UserDataBlock(object):
	
	def __init__(self, user):
		self.user = user
		self.uID = str(user.id)
		self.uValues = getSimuGachaData()
		self.__check_if_user_in_uValues()
		
	def UpdateUserWithRollResult(self, rollReport):
		self.__increment_ssrServant_count(rollReport.ssrServantRolled)
		self.__increment_ssrCE_count(rollReport.ssrCERolled)
		self.__add_to_servants_rolled(rollReport.servantRolled)
		self.__add_to_ce_rolled(rollReport.ceRolled)
		self.__set_user_last_roll(rollReport.rollSummary)
		self.UpdateControlWithResult(rollReport)
		self.__set_user_data()
		
	def UpdateControlWithResult(self, rollReport):
		if requiresSQFlag:
			self.uValues["control"]["rollsTotal"]+=len(rollReport.rollSummary)
			self.uValues["control"]["sqspent"]+=(3*len(rollReport.rollSummary))
		else:
			self.uValues["control"]["freerollsTotal"]+=len(rollReport.rollSummary)
			self.uValues["control"]["freesqspent"]+=(3*len(rollReport.rollSummary))			
		
	def __set_user_data(self):
		setSimuGachaData(self.uValues)
		
	def __check_if_user_in_uValues(self):
		if not self.uID in self.uValues:
			print("\nUserID: [" + self.uID + "] has been added to the Grand Order of things.")
			self.__create_new_user_keys()
		
	def __create_new_user_keys(self):
		newUser = {
        'sqcurrent' : 300,
        'sqtotal' : 300,
        'loginchain' : 0,
		'logintoken' : 0,
        'servantsrolled' : [],
        'cerolled' : [],
        'bestroll' : [],
        'lastroll': [],
		'ssrservantcount': 0,
		'ssrcecount': 0,
		'profilecard' : ""
		}
		self.uValues[self.uID] = newUser
		self.__set_user_data()
		
	def __add_to_servants_rolled(self, rollList):
		self.uValues[self.uID]["servantsrolled"] += [item for item in list(set(rollList)) if item not in self.uValues[self.uID]["servantsrolled"]]
	
	def __get_unique_servant_count(self):
		return len(self.uValues[self.uID]["servantsrolled"])
	
	def __get_unique_ce_count(self):
		return len(self.uValues[self.uID]["cerolled"])
		
	def __add_to_ce_rolled(self, rollList):
		self.uValues[self.uID]["cerolled"] += [item for item in list(set(rollList)) if item not in self.uValues[self.uID]["cerolled"]]
		
	def __get_servants_rolled(self):
		return self.uValues[self.uID]["servantsrolled"]
		
	def __get_ce_rolled(self):
		return self.uValues[self.uID]["cerolled"]
		
	def __increment_ssrServant_count(self, amount):
		self.uValues[self.uID]["ssrservantcount"]+=amount
		
	def __get_ssrServants_rolled(self):
		return self.uValues[self.uID]["ssrservantcount"]
	
	def __increment_ssrCE_count(self, amount):
		self.uValues[self.uID]["ssrcecount"]+=amount
		
	def __get_ssrCE_rolled(self):
		return self.uValues[self.uID]["ssrcecount"]
	
	def user_rolled(self, amount):
		if self.uValues[self.uID]["sqcurrent"] < amount and requiresSQFlag:
			return False
		if requiresSQFlag:
			self.uValues[self.uID]["sqcurrent"]-=amount
		self.__set_user_data()
		return True
		
	def get_sqcurrent(self):
		return self.uValues[self.uID]["sqcurrent"]
		
	def increment_sqtotal(self, amount):
		self.uValues[self.uID]["sqcurrent"]+=amount
		self.uValues[self.uID]["sqtotal"]+=amount
		self.__set_user_data()
		
	def __get_sqspent(self):
		sqspent = self.uValues[self.uID]["sqtotal"] - self.uValues[self.uID]["sqcurrent"]
		rollsdone = int(sqspent/3)
		return rollsdone,sqspent
		
	def __set_user_last_roll(self, rollList):
		self.uValues[self.uID]["lastroll"] = rollList
		self.__set_user_data()
		
	def set_user_best_roll(self):
		self.uValues[self.uID]["bestroll"] = self.uValues[self.uID]["lastroll"]
		self.__set_user_data()
		
	def show_user_best_roll(self):
		if len(self.uValues[self.uID]["bestroll"]) != 0:
			return self.uValues[self.uID]["bestroll"]
			
	def user_logged_in(self):
		return self.__increment_login_chain()
		
	def __increment_login_chain(self):
		prefixMsg = ""
		if not self.uValues[self.uID]["logintoken"]==1:
			self.uValues[self.uID]["loginchain"]+=1
			self.uValues[self.uID]["logintoken"]=1
			baseMultiplier=7 if self.uValues[self.uID]["loginchain"]>7 else self.uValues[self.uID]["loginchain"]
			totalSQ = 3+(1*baseMultiplier)
			self.increment_sqtotal(totalSQ)
			self.__set_user_data()
			prefixMsg = "Thank you for logging in.\nYou've recieved **{} Saint Quartz** for your login+streak.\nCurrent Saint Quartz: {}".format(totalSQ,self.get_sqcurrent())
		else:
			prefixMsg = "You've already logged in today."
		return "{}\nYour login streak is currently {} day(s).".format(prefixMsg, self.uValues[self.uID]["loginchain"])
		
	def set_user_profile_card(self, path):
		self.uValues[self.uID]["profilecard"]=path
		self.__set_user_data()
			
	def generate_user_simugacha_summary_embed(self):
		ssrCount = self.__get_ssrServants_rolled()
		ssrCECount = self.__get_ssrCE_rolled()
		rollCount,spentsq = self.__get_sqspent()
		quartzCount = self.get_sqcurrent()
		userServantCount = self.__get_unique_servant_count()
		userCECount = self.__get_unique_ce_count()
		totalServants = self.uValues["control"]["totalservants"]
		totalCE = self.uValues["control"]["totalce"]
		outString = ""
		if requiresSQFlag:
			outString = "Saint Quartz Spent: {} ({} rolls)\nCurrent Saint Quartz: {}\n".format(spentsq,rollCount,quartzCount)
		outString += "SSR Servants Rolled: {}\nSSR CE Rolled: {}".format(ssrCount,ssrCECount)
		em = discord.Embed(title="Gacha Stats for {}".format(self.user.name), description=outString, colour=0x00AE86)
		em.add_field(name="Completion Rate", value="Servant Dex: {}/{} (~{}%)\nCraft Essence Dex: {}/{} (~{}%)".format(userServantCount, totalServants, int((userServantCount/totalServants)*100), userCECount,totalCE,int((userCECount/totalCE)*100)))
		em.set_footer(text="You should try to obtain every servant.")
		try:
			em.set_thumbnail(url=self.user.avatar_url)
		except:
			pass
		return em

class SimuGacha(commands.Cog):

	def __init__(self,bot):
		self.bot=bot
		self.enableGachaRolls = True
		self.maintenanceMessage = "Currently down for maintenance. Sorry. It'll only be a bit."
		self.SGacha = StoryPool()
		self.LGacha = LimitedPools()
		self.donateMessage = "Please remember to donate if you can ({}donate)".format(self.bot.prefix)
		self.botLaunch = datetime.now()
		self.JST = pytz.timezone("Asia/Tokyo")
		self.EST = pytz.timezone("Canada/Eastern")
		if requiresSQFlag:
			self.rewardsGiven = self.JST.localize(datetime(year=_botLaunch.year, month=_botLaunch.month, day=_botLaunch.day, hour=4, minute=00, second=00))
			asyncio.ensure_future(self.LoginTokenResetter())
		
	async def LoginTokenResetter(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			try:
				await self.timer_for_daily_reset()	
			except Exception as e:
				print("Token Resetter Crash: {}".format(e))
		print("Terminating Token Resetter")
		
	async def timer_for_daily_reset(self):
		await self.bot.wait_until_ready()
		preString = "Starting Token Reset Timer..."
		print("{:<35}".format(preString), end="")
		print("\tSuccess")
		doNothing = True
		while doNothing:
			diff = self.rewardsGiven - self.EST.localize(datetime.now())
			if diff.total_seconds() <= 0:
				self.rewardsGiven = self.rewardsGiven + timedelta(days=1)
			else:
				diff = self.rewardsGiven - self.EST.localize(datetime.now())
				await asyncio.sleep(diff.total_seconds())
				print("Login Token Reset")
				uValues = getSimuGachaData()
				for user in uValues:
					if not user == "control":
						if uValues[user]["logintoken"] != 0:
							print("Chain kept")
							uValues[user]["logintoken"]=0
						else:
							print("Chain broken")
							uValues[user]["loginchain"]=0
				setSimuGachaData(uValues)
				
	async def simugacha_creates_embed_to_post(self,type,gachaName,user,imageurl):
		em=discord.Embed(title="{} {} Roll Results".format(gachaName,type),description="Rolled by: {}".format(user.name))
		em.set_footer(text=self.donateMessage)
		try:
			em.set_thumbnail(url=user.avatar_url)
		except:
			pass
		em.set_image(url=await self.return_attach_url(imageurl))
		return em
		
	async def return_attach_url(self,uri):
		burnerAttachmentChannel = self.bot.get_channel(320188991687229441)#318760533949939715)
		attachmentMessage = await burnerAttachmentChannel.send(file=discord.File(uri, filename="roll.jpg"))
		attachmentURL = attachmentMessage.attachments[0].url
		os.remove( uri )
		return attachmentURL
		
	def generate_console_output(self,user,guild,pooltype,rolls):
		print("\n@{}\nUser: {}\nGuild: {}\n{} | {}".format(str(datetime.now())[:str(datetime.now()).index(".")], user.id,guild.id,pooltype,rolls))
		
	@commands.group()
	async def gacha(self, ctx):
		await ctx.trigger_typing()
		if ctx.invoked_subcommand is None:
			em = discord.Embed(title="General SimuGacha Information", description="-The {0} command uses the 'official' rates.\n-This bot accepts `-yolo` as an argument.\n-Limited gachas are kept up-to-date.\n------------".format("gacha"), colour=0x00AE86)
			em.set_footer(text=self.donateMessage)
			em.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
			em.add_field(name="Rates", value="Servant Pull Rate: **20%**\nCE Pull Rate: **80%**\n\nCurrent Servant Rates:\n`SSR {}.0%` | `SR {}.0%` | `R 40.0%`\n\nCurrent CE Rates:\n`SSR {}.0%` | `SR {}.0%` | `R 40.0%`\n------------".format(1, 3, 4, 12))
			em.add_field(name="Example Gacha Commands", value="`{0}{1} -story`\n`{0}{1} -lim 0 -yolo`\n`{0}{1} -lim 2`\n`{0}{1} -story -yolo`\nThe number next to `lim` can be found by using `{0}{1} -list` command".format(self.bot.prefix, "gacha"))
			em.add_field(name="User Data Commands", value="`{0}{1} -list` will display all active limited pools\n`{0}{1} -stats` will show your SimuGacha info\n`{0}{1} -save` saves your most recent roll\n`{0}{1} -show` shows your saved roll\n`{0}{1} -limcheck #` will show rateup servants/ce".format(self.bot.prefix, "gacha"))
			if requiresSQFlag:
				em.add_field(name="Information", value="All users will start with 300 Saint Quartz. You can obtain Saint Quartz with daily logins `{}gacha -login`\n\nLogins give 3sq per day, with 1 extra per chained day up to a max of 10 per day.".format(self.bot.prefix))
				em.add_field(name="Why is this feature no longer unlimited?", value="People are using this bot on over nearly a thousand servers. Due to this, I must restrict it. I apologize. If you want to see it open back up, use `{}donate`".format(self.bot.prefix))
			else:
				em.add_field(name="Information", value="Saint Quartz requirements are currently **disabled**. Please enjoy the SimuGacha.".format(self.bot.prefix))
			await ctx.send(embed=em)
			
	@gacha.command(name="-login")
	async def simugacha_user_logged_in(self,ctx):
		if requiresSQFlag:
			thisUser = UserDataBlock(ctx.message.author)
			await ctx.send(embed=discord.Embed(description=thisUser.user_logged_in()))
		else:
			await ctx.send(embed=discord.Embed(description="Saint Quartz is not currently required to use the SimuGacha, thus login is frozen."))
		
	@gacha.command(name="-stats")
	async def simugacha_displays_stats_for_user(self,ctx):
		thisUser = UserDataBlock(ctx.message.author)
		await ctx.send(embed=thisUser.generate_user_simugacha_summary_embed())

	@gacha.command(name="-save")
	async def simugacha_saves_last_user_roll(self,ctx):
		thisUser = UserDataBlock(ctx.message.author)
		thisUser.set_user_best_roll()
		await ctx.send(embed=discord.Embed(description="Your last roll has been saved."))
		
	@gacha.command(name="-show")
	async def simugacha_shows_last_user_roll(self,ctx):
		thisUser = UserDataBlock(ctx.message.author)
		roll = thisUser.show_user_best_roll()
		imageurl=self.SGacha.generate_roll_snapshot_image(roll,"USERSHOW {}".format(ctx.message.author.id),ctx.message.author.id)
		em=discord.Embed(title="{}'s Saved Roll".format(ctx.message.author.name))
		em.set_footer(text="Worth bragging about?")
		try:
			em.set_thumbnail(url=user.avatar_url)
		except:
			pass
		em.set_image(url=await self.return_attach_url(imageurl))
		await ctx.send(embed=em)

	@gacha.command(name="-story")
	@commands.cooldown(rate=5, per=10, type=BucketType.user)
	async def simugacha_rolls_story(self, ctx, *, args=""):
		thisUser = UserDataBlock(ctx.message.author)
		if "-yolo" in args:
			if thisUser.user_rolled(3):
				result=self.SGacha.yolo_roll(thisUser.uID)
				thisUser.UpdateUserWithRollResult(result)
				await ctx.send(embed=await self.simugacha_creates_embed_to_post("Yolo", "Story",ctx.message.author,result.imagePath))
				self.generate_console_output(ctx.message.author,ctx.message.guild,"Story","Yolo")
			else:
				await ctx.send(embed=discord.Embed(description="You require at least 3sq to do a single roll."))
		else: 
			if thisUser.user_rolled(30):
				result=self.SGacha.multi_roll(thisUser.uID)
				thisUser.UpdateUserWithRollResult(result)
				await ctx.send(embed=await self.simugacha_creates_embed_to_post("Multi", "Story",ctx.message.author,result.imagePath))
				self.generate_console_output(ctx.message.author,ctx.message.guild,"Story","Multi")
			else:
				await ctx.send(embed=discord.Embed(description="You require at least 30sq to do a multi roll."))
		
	@gacha.command(name="-lim")
	@commands.cooldown(rate=5, per=10, type=BucketType.user)
	async def simugacha_rolls_limpool(self, ctx, *, args=""):
		rippedNumber = [int(s) for s in args.split() if s.isdigit()]
		if len(rippedNumber)>0:rippedNumber=rippedNumber[0]
		thisUser = UserDataBlock(ctx.message.author)
		if rippedNumber <= self.LGacha.return_pool_count(): 
			if "-yolo" in args:
				if thisUser.user_rolled(3):
					result=self.LGacha.yolo_roll(rippedNumber, thisUser.uID)
					thisUser.UpdateUserWithRollResult(result)
					await ctx.send(embed=await self.simugacha_creates_embed_to_post("Yolo", self.LGacha.return_pool_name(rippedNumber),ctx.message.author,result.imagePath))
					self.generate_console_output(ctx.message.author,ctx.message.guild,self.LGacha.return_pool_name(rippedNumber),"Yolo")
				else:
					await ctx.send(embed=discord.Embed(description="You require at least 3sq to do a single roll."))
			else:
				if thisUser.user_rolled(30):
					result=self.LGacha.multi_roll(rippedNumber, thisUser.uID)
					thisUser.UpdateUserWithRollResult(result)
					await ctx.send(embed=await self.simugacha_creates_embed_to_post("Multi", self.LGacha.return_pool_name(rippedNumber),ctx.message.author,result.imagePath))
					self.generate_console_output(ctx.message.author,ctx.message.guild,self.LGacha.return_pool_name(rippedNumber),"Multi")
				else:
					await ctx.send(embed=discord.Embed(description="You require at least 30sq to do a multi roll.")) 
		else:
			await ctx.send(embed=discord.Embed(description="You must pick a valid limited pool. Please use `{}gacha -list` to see what's available.".format(self.bot.prefix)))
			return
		
	@gacha.command(name="-limcheck")
	@commands.cooldown(rate=5, per=10, type=BucketType.user)
	async def simugacha_checks_limpool(self, ctx, limarg):
		if limarg.isdigit():
			if int(limarg) <= self.LGacha.return_pool_count():
				print(self.LGacha.return_rateup_list(int(limarg)))
		else:
			await ctx.send(embed=discord.Embed(description="You must pick a valid limited pool. Please use `{}gacha -list` to see what's available.".format(self.bot.prefix)))
		
	@gacha.command(name="-list")
	@commands.cooldown(rate=5, per=10, type=BucketType.user)
	async def simugacha_shows_active_limpools(self, ctx):
		outStr = ""
		for index,poolName in enumerate(self.LGacha.return_pool_names()):
			outStr += "[{}] {}\n".format(index,poolName)
		em = discord.Embed(title="Current Limited Gacha Pools", description="```" + outStr + "```", colour=0x00AE86)
		em.set_footer(text="Limited Pools are subject to change and trolling with no warning.")
		try:
			em.set_thumbnail(url='http://i.imgur.com/r3ozyII.png')
		except:
			pass
		em.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
		await ctx.send(embed=em)
		
	@gacha.command(name="-reload")
	@commands.check(is_owner)
	async def simugacha_reloads_limpools(self, ctx):
		self.LGacha = None
		self.LGacha = LimitedPools()
		
class Pool:

	SSRChance = 1
	SRChance = 3
	SSRCEChance = 4
	SRCEChance = 12

	FSSRChance = 11
	FSRChance = 33
	FSSRCEChance = 18
	FSRCEChance = 38
	
	GSSRChance = 1
	GSRChance = 3
	GRChance = 40

	def __init__(self):
		# below is generic pool holders
		self.ssrSPool = []
		self.ssrCPool = []
		self.srSPool = []
		self.srCPool = []
		self.rSPool = []
		self.rCPool = []
		self.poolPath="pools\\"
		self.defaultPath="base\\"
		self.eventPath="event\\"
		self.limitedPath="limited\\"
		self.servantPath="gatcha\\servant\\"
		self.cePath="gatcha\\ce\\"
		self.__generate_default_data()
		
	def __generate_default_data(self):
		#SSR
		self.ssrSPool = returnJson(self.poolPath + self.defaultPath, "defaultSSRservant")
		self.ssrCPool = returnJson(self.poolPath + self.defaultPath, "defaultSSRce")
		
		#SR
		self.srSPool = returnJson(self.poolPath + self.defaultPath, "defaultSRservant")
		self.srCPool = returnJson(self.poolPath + self.defaultPath, "defaultSRce")
		
		#R
		self.rSPool = returnJson(self.poolPath + self.defaultPath, "defaultRservant")
		self.rCPool = returnJson(self.poolPath + self.defaultPath, "defaultRce")
		
	def generate_roll_snapshot_image(self,roll,tscontent,userID):
		if noImageFlag:
			return 'gatcha\\urolls\\{}_roll.png'.format(userID)
		if len(roll)>1 and len(roll)<10:
			return False
		for x in range(len(roll)):
			if not os.path.isfile(roll[x]):
				print("Missing file @: {} | {}".format(roll[x],tscontent))
				roll[x] = "gatcha\\noicon.png"
		length=len(roll)
		imageCount = len(roll)
		images = list(map(Image.open, roll))
		widths,heights = zip(*(i.size for i in images))
		if length % 2 == 0:
			total_width = int(sum(widths) / 2)
		else:
			total_width = int ((sum(widths) / length) * int(math.ceil(length/2)))
		max_height = max(heights) * 2 if len(roll)>1 else max(heights)
		new_im = Image.new('RGBA', (total_width,max_height), (255,0,0,0))
				
		x_offset = 0
		curCount = 0
		curRow = 0
		for im in images:
			new_im.paste(im, (x_offset,curRow))
			x_offset += im.size[0]
			curCount += 1
			if curCount == int(imageCount/2):
				curRow = int(max_height/2)
				x_offset = 0
		new_im.save('gatcha\\urolls\\{}_roll.png'.format(userID))
		return 'gatcha\\urolls\\{}_roll.png'.format(userID)
		
	
class LimitedPools(Pool):

	def __init__(self):
		Pool.__init__(self)
		#print("Default Pool initialized.")
		self.poolFiles = self.__populate_active_json_list()
		self.rateupLimitedSSR = []
		self.rateupSSRServants = []
		self.rateupSRServants = []
		self.rateupRServants = []
		self.rateupSSRCE = []
		self.rateupSRCE = []
		self.rateupRCE = []
		self.poolNames = []
		self.LimitedServantRate = 25
		self.LimitedCERate = 15
		self.__generate_pool_data(self.poolFiles)
		
	def debug(self):
		print(self.rateupRServants)
		print(self.rateupSSRServants)
		
	def return_pool_names(self):
		return self.poolNames
		
	def return_pool_name(self,index):
		return self.poolNames[index]
		
	def return_pool_count(self):
		return len(self.poolNames)-1
		
	def __populate_active_json_list(self):
		fNames = []
		for filename in os.listdir(self.poolPath + self.limitedPath):
			if filename.endswith(".json"):
				uValues = returnJsonUnicode(self.poolPath + self.limitedPath, filename)
				if uValues["control"]["active"] == "True":
					fNames.append(filename[:-5])
		return fNames
					
	def __generate_pool_data(self, fileNames):
		for jsonFile in fileNames:
			uValues = returnJsonUnicode(self.poolPath + self.limitedPath, jsonFile)
		
			self.poolNames.append(uValues["ssrGatchaName"])
		
			#SSR
			if uValues["ssrServantrateup"] == [""]:
				self.rateupSSRServants.append(None)
			else:
				self.rateupSSRServants.append(uValues["ssrServantrateup"])
			if uValues["ssrCErateup"] == [""]:
				self.rateupSSRCE.append(None)
			else:
				self.rateupSSRCE.append(uValues["ssrCErateup"])
			
			#SR
			if uValues["srServantrateup"] == [""]:
				self.rateupSRServants.append(None)
			else:
				self.rateupSRServants.append(uValues["srServantrateup"])
			if uValues["srCErateup"] == [""]:
				self.rateupSRCE.append(None)
			else:
				self.rateupSRCE.append(uValues["srCErateup"])
			
			#R
			if uValues["rServantrateup"] == [""]:
				self.rateupRServants.append(None)
			else:
				self.rateupRServants.append(uValues["rServantrateup"])
			if uValues["rCErateup"] == [""]:
				self.rateupRCE.append(None)
			else:
				self.rateupRCE.append(uValues["rCErateup"])
			
			#Limited
			if uValues["rCErateup"] == [""]:
				self.rateupLimitedSSR.append(None)
			else:
				self.rateupLimitedSSR.append(uValues["ssrLim"])
		
	def yolo_roll(self,pool,im_id):
		results = self.__single_roll(pool)
		results.imagePath = self.generate_roll_snapshot_image(results.rollSummary,"LIM{} -YOLO".format(pool), im_id)
		return results
		
	def multi_roll(self,pool,im_id):
		totalResult = RollResult(0,0,0,0,0,0,[],[],0,[])
		rollCount = 11
		if massTestFlag: rollCount = massTestValue
		retList = []
		flag=0
		for x in range(0,rollCount): #11, 10+1
			if x==1:flag=1
			if x==2:flag=None
			totalResult += self.__single_roll(pool,flag)
		#random.shuffle()
		if massTestFlag: 
			print("Sample size of below rollset was {}".format(rollCount))
			for key in sorted(dict(Counter(totalResult.rollSummary).items())): print("{} : {}".format(key,dict(Counter(totalResult.rollSummary))[key]))
			return ""
		totalResult.imagePath = self.generate_roll_snapshot_image(totalResult.rollSummary,"LIM{}".format(pool), im_id)
		return totalResult
		
	def __single_roll(self, pool, forcedRarity=None):
		#determine rarity using base rates
		rollReport = RollResult(0,0,0,0,0,0,[],[],0,[])
		result = ""
		if forcedRarity==0:
			ranPull = random.randint(0,Pool.FSSRChance+Pool.FSSRCEChance+Pool.FSRChance+Pool.FSRCEChance)
			if ranPull <= Pool.FSSRChance:
				result = "SSRS"
			elif ranPull <= Pool.FSSRChance + Pool.FSSRCEChance:
				result = "SSRC"
			elif ranPull <= Pool.FSSRChance + Pool.FSSRCEChance + Pool.FSRChance:
				result = "SRS"
			else:
				result = "SRC"
		elif forcedRarity==1:
			ranPull = random.randint(0,Pool.GSSRChance+Pool.GSRChance+Pool.GRChance)
			if ranPull <= Pool.GSSRChance:
				result = "SSRS"
			elif ranPull <= Pool.GSSRChance + Pool.GSRChance:
				result = "SRS"
			else:
				result = "RS"
		else:
			if random.randint(1,5)==0: #20% chance of servant
				ranPull = random.randint(1,100) #1% chance of ssr
				if ranPull <= Pool.SSRChance:
					result = "SSRS"
				elif ranPull <= Pool.SSRChance + Pool.SRChance:
					result = "SRS"
				else:
					result = "RS"
			else:
				ranPull = random.randint(1,100)
				if ranPull <= Pool.SSRCEChance:
					result = "SSRC"
				elif ranPull <= Pool.SSRCEChance + Pool.SRCEChance:
					result = "SRC"
				else:
					result = "RC"
		if result == "SSRS": 
			item="{}{}.png".format(self.servantPath, self.__return_ssr_servant(pool))
			rollReport.ssrServantRolled+=1
			rollReport.servantRolled.append(item.split("\\")[2][:-4])
		elif result == "SSRC": 
			item="{}{}.png".format(self.cePath, self.__return_ssr_ce(pool))
			rollReport.ssrCERolled+=1
			rollReport.ceRolled.append(item.split("\\")[2][:-4])
		elif result == "SRS": 
			item="{}{}.png".format(self.servantPath, self.__return_sr_servant(pool))
			rollReport.srServantRolled+=1
			rollReport.servantRolled.append(item.split("\\")[2][:-4])
		elif result == "SRC": 
			item="{}{}.png".format(self.cePath, self.__return_sr_ce(pool))
			rollReport.srCERolled+=1
			rollReport.ceRolled.append(item.split("\\")[2][:-4])
		elif result == "RS": 
			item="{}{}.png".format(self.servantPath, self.__return_r_servant(pool))
			rollReport.rServantRolled+=1
			rollReport.servantRolled.append(item.split("\\")[2][:-4])
		elif result == "RC": 
			item="{}{}.png".format(self.cePath, self.__return_r_ce(pool))
			rollReport.rCERolled+=1
			rollReport.ceRolled.append(item.split("\\")[2][:-4])
		rollReport.rollSummary.append(item)
		return rollReport
		
	def return_rateup_list(self, poolint):
		cardList = []
		servantList = [self.rateupLimitedSSR[poolint], self.rateupSSRServants[poolint], self.rateupSRServants[poolint], self.rateupRServants[poolint]]
		print(servantList)
		ceList = [self.rateupSSRCE[poolint], self.rateupSRCE[poolint], self.rateupRCE[poolint]]
		print(ceList)
		for servants in servantList:
			if servants:
				for entry in servants:
					if not entry == "":
						cardList.append("{}{}.png".format(self.servantPath, entry))
		for essences in ceList:
			if essences:
				for entry in essences:
					if not entry == "":
						cardList.append("{}{}.png".format(self.cePath, entry))
		return cardList
		
	def __return_ssr_servant(self, pool):
		if self.rateupLimitedSSR[pool] and self.rateupSSRServants[pool]:
			if random.randint(0,4)<=3:
				if massTestFlag: return "rateupLimitedSSR"
				return random.choice(self.rateupLimitedSSR[pool])
			else:
				if massTestFlag: return "rateupSSR"
				return random.choice(self.rateupSSRServants[pool]+self.ssrSPool)
		elif self.rateupLimitedSSR[pool] and not self.rateupSSRServants[pool]:
			if random.randint(0,4)<=3:
				if massTestFlag: return "rateupLimitedSSR"
				return random.choice(self.rateupLimitedSSR[pool])
			else:
				if massTestFlag: return "ssrSPool"
				return random.choice(self.ssrSPool)
		elif not self.rateupLimitedSSR[pool] and self.rateupSSRServants[pool]:
			if massTestFlag: return "rateupSSR"
			return random.choice(self.rateupSSRServants[pool]+self.ssrSPool)
		else:
			if massTestFlag: return "ssrSPool"
			return random.choice(self.ssrSPool)
		
	def __return_sr_servant(self, pool):
		result = random.choices(
		["lim","non"],[self.LimitedServantRate,100-self.LimitedServantRate],k=1)[0]
		if result=="lim" and self.rateupSRServants[pool]:
			if massTestFlag: return "rateupSRServantsLim"
			return random.choice(self.rateupSRServants[pool])
		elif self.rateupSRServants[pool]:
			if massTestFlag: return "rateupSRServants"
			return random.choice(self.rateupSRServants[pool]+self.srSPool)
		else:
			if massTestFlag: return "srSPool"
			return random.choice(self.srSPool)
			
	def __return_r_servant(self, pool):
		result = random.choices(
		["lim","non"],[self.LimitedServantRate,100-self.LimitedServantRate],k=1)[0]
		if result=="lim" and self.rateupRServants[pool]:
			if massTestFlag: return "rateupRServantsLim"
			return random.choice(self.rateupRServants[pool])
		elif self.rateupRServants[pool]:
			if massTestFlag: return "rateupRServants"
			return random.choice(self.rateupRServants[pool]+self.rSPool)
		else:
			if massTestFlag: return "rSPool"
			return random.choice(self.rSPool)
	
	def __return_ssr_ce(self, pool):
		result = random.choices(
		["lim","non"],[self.LimitedCERate,100-self.LimitedCERate],k=1)[0]
		if result=="lim" and self.rateupSSRCE[pool]:
			if massTestFlag: return "rateupSSRCELim"
			return random.choice(self.rateupSSRCE[pool])
		elif self.rateupSSRCE[pool]:
			if massTestFlag: return "rateupSSRCE"
			return random.choice(self.rateupSSRCE[pool]+self.ssrCPool)
		else:
			if massTestFlag: return "ssrCPool"
			return random.choice(self.ssrCPool)
	
	def __return_sr_ce(self, pool):
		result = random.choices(
		["lim","non"],[self.LimitedCERate,100-self.LimitedCERate],k=1)[0]
		if result=="lim" and self.rateupSRCE[pool]:
			if massTestFlag: return "rateupSRCELim"
			return random.choice(self.rateupSRCE[pool])
		elif self.rateupSRCE[pool]:
			if massTestFlag: return "rateupSRCE"
			return random.choice(self.rateupSRCE[pool]+self.srCPool)
		else:
			if massTestFlag: return "srCPool"
			return random.choice(self.srCPool)
	
	def __return_r_ce(self, pool):
		result = random.choices(
		["lim","non"],[self.LimitedCERate,100-self.LimitedCERate],k=1)[0]
		if result=="lim" and self.rateupRCE[pool]:
			if massTestFlag: return "rateupRCELim"
			return random.choice(self.rateupRCE[pool])
		elif self.rateupRCE[pool]:
			if massTestFlag: return "rateupRCE"
			return random.choice(self.rateupRCE[pool]+self.rCPool)
		else:
			if massTestFlag: return "rCPool"
			return random.choice(self.rCPool)	
	
	
class StoryPool(Pool):
	
	def __init__(self):
		Pool.__init__(self)
		#print("Default Pool initialized.")
		self.__merge_default_pool_with_storylock()
		#print("Default Pool merged with Storylocked.")
		
	def __merge_default_pool_with_storylock(self):
		self.ssrSPool += returnJson(self.poolPath + self.defaultPath, "storySSRservant")
		self.ssrCPool += returnJson(self.poolPath + self.defaultPath, "storySSRce")
		self.srSPool += returnJson(self.poolPath + self.defaultPath, "storySRservant")
		self.srCPool += returnJson(self.poolPath + self.defaultPath, "storySRce")
		self.rSPool += returnJson(self.poolPath + self.defaultPath, "storyRservant")
		self.rCPool += returnJson(self.poolPath + self.defaultPath, "storyRce")
		return
		
	def yolo_roll(self, im_id):
		results = self.__single_roll()
		results.imagePath = self.generate_roll_snapshot_image(results.rollSummary,"STORY -YOLO", im_id)
		return results
		
	def multi_roll(self, im_id):
		totalResult = RollResult(0,0,0,0,0,0,[],[],0,[])
		rollCount = 11
		if massTestFlag: rollCount = massTestValue
		retList = []
		flag=0
		for x in range(0,rollCount): #11, 10+1
			if x==1:flag=1
			if x==2:flag=None
			totalResult += self.__single_roll(flag)
		#random.shuffle()
		if massTestFlag: 
			print("Sample size of below rollset was {}".format(rollCount))
			for key in sorted(dict(Counter(totalResult.rollSummary).items())): print("{} : {}".format(key,dict(Counter(totalResult.rollSummary))[key]))
			return ""
		totalResult.imagePath = self.generate_roll_snapshot_image(totalResult.rollSummary,"STORY", im_id)
		return totalResult
		
	def __single_roll(self, forcedRarity=None):
		#determine rarity using base rates
		rollReport = RollResult(0,0,0,0,0,0,[],[],0,[])
		result = ""
		if forcedRarity==0:
			ranPull = random.randint(0,Pool.FSSRChance+Pool.FSSRCEChance+Pool.FSRChance+Pool.FSRCEChance)
			if ranPull <= Pool.FSSRChance:
				result = "SSRS"
			elif ranPull <= Pool.FSSRChance + Pool.FSSRCEChance:
				result = "SSRC"
			elif ranPull <= Pool.FSSRChance + Pool.FSSRCEChance + Pool.FSRChance:
				result = "SRS"
			else:
				result = "SRC"
		elif forcedRarity==1:
			ranPull = random.randint(0,Pool.GSSRChance+Pool.GSRChance+Pool.GRChance)
			if ranPull <= Pool.GSSRChance:
				result = "SSRS"
			elif ranPull <= Pool.GSSRChance + Pool.GSRChance:
				result = "SRS"
			else:
				result = "RS"
		else:
			if random.randint(1,5)==0: #20% chance of servant
				ranPull = random.randint(1,100) #1% chance of ssr
				if ranPull <= Pool.SSRChance:
					result = "SSRS"
				elif ranPull <= Pool.SSRChance + Pool.SRChance:
					result = "SRS"
				else:
					result = "RS"
			else:
				ranPull = random.randint(1,100)
				if ranPull <= Pool.SSRCEChance:
					result = "SSRC"
				elif ranPull <= Pool.SSRCEChance + Pool.SRCEChance:
					result = "SRC"
				else:
					result = "RC"
		if result == "SSRS": 
			item="{}{}.png".format(self.servantPath, self.__return_ssr_story_servant())
			rollReport.ssrServantRolled+=1
			rollReport.servantRolled.append(item.split("\\")[2][:-4])
		elif result == "SSRC": 
			item="{}{}.png".format(self.cePath, self.__return_ssr_story_ce())
			rollReport.ssrCERolled+=1
			rollReport.ceRolled.append(item.split("\\")[2][:-4])
		elif result == "SRS": 
			item="{}{}.png".format(self.servantPath, self.__return_sr_story_servant())
			rollReport.srServantRolled+=1
			rollReport.servantRolled.append(item.split("\\")[2][:-4])
		elif result == "SRC": 
			item="{}{}.png".format(self.cePath, self.__return_sr_story_ce())
			rollReport.srCERolled+=1
			rollReport.ceRolled.append(item.split("\\")[2][:-4])
		elif result == "RS": 
			item="{}{}.png".format(self.servantPath, self.__return_r_story_servant())
			rollReport.rServantRolled+=1
			rollReport.servantRolled.append(item.split("\\")[2][:-4])
		elif result == "RC": 
			item="{}{}.png".format(self.cePath, self.__return_r_story_ce())
			rollReport.rCERolled+=1
			rollReport.ceRolled.append(item.split("\\")[2][:-4])
		rollReport.rollSummary.append(item)
		return rollReport
		
	def __return_ssr_story_servant(self):
		return random.choice(self.ssrSPool)
		
	def __return_sr_story_servant(self):
		return random.choice(self.srSPool)
	
	def __return_r_story_servant(self):
		return random.choice(self.rSPool)
	
	def __return_ssr_story_ce(self):
		return random.choice(self.ssrCPool)
	
	def __return_sr_story_ce(self):
		return random.choice(self.srCPool)
	
	def __return_r_story_ce(self):
		return random.choice(self.rCPool)

def setup(bot):
	bot.add_cog(SimuGacha(bot))