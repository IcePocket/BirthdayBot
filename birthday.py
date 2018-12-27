import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import json
import platform
import datetime
import calendar
import pytz
import re
import pymongo
from pymongo import MongoClient

config_path = None
config_file = open(config_path, "r")
config_data = json.load(config_file)

timezones_link = config_data["timezones_link"]
db_client = pymongo.MongoClient(config_data["mongo_address"])
database = db_client[""]
usersCollection = database[""]
serversCollection = database[""]

def get_token(file_name):
	with open(file_name, "r") as f:
		token = f.read()
	return token

def insert_user(user_object):
    usersCollection.insert_one(user_object)

def insert_server(server_object):
    serversCollection.insert_one(server_object)

def update_user(id, new_values):
    usersCollection.update_one({"id" : id}, {"$set": new_values})

def update_server(id, new_values):
    serversCollection.update_one({"id" : id}, {"$set": new_values})

def remove_user(id):
    usersCollection.delete_one({"id" : id})

def remove_server(id):
    serversCollection.delete_one({"id" : id})

def user_exists(id):
    return usersCollection.find({"id" : id}).count() > 0

def server_exists(id):
    return serversCollection.find({"id" : id}).count() > 0

def get_bd_channel_id(server_id):
    return serversCollection.find_one({"id" : server_id})["birthday_channel_id"]

def get_users_data():
    return usersCollection.find()

def get_servers_data():
    return serversCollection.find()

def get_users_count():
    return usersCollection.find().count()

def get_user_object(id):
    return usersCollection.find_one({"id" : id})

def get_server_object(id):
    return serversCollection.find_one({"id" : id})

def all_are_integers(args):
    for arg in args:
        if not arg.isdigit():
            return False
    return True

def is_leap_year(year):
    if year % 4 == 0:
        if year % 100 == 0:
            if year % 400 == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def check_date(year, month, day):
    if (not 1970 <= year <= datetime.datetime.now().year - 5) or (not 1 <= month <= 12) or (not 1 <= day <= 31):
        return False
    elif month in [4, 6, 9, 11] and day > 30:
        return False
    elif month == 2 and (day > 29 or (day == 29 and not is_leap_year(year))):
        return False
    return True

def is_channel_mention(arg):
	return bool(re.search(r'<#\d{18}>', arg))

def get_age_with_postfix(age):
    age_str = ""
    if age % 10 == 1 and age // 10 != 1:
        age_str = f"{age}st"
    elif age % 10 == 2 and age // 10 != 1:
	    age_str = f"{age}nd"
    elif age % 10 == 3 and age // 10 != 1:
	    age_str = f"{age}rd"
    else:
	    age_str = f"{age}th"
    return age_str

bot = Bot(description="This is a bot whose main purpose is to announce birthdays", command_prefix="~", pm_help = False)
bot.remove_command('help')

help_embed = discord.Embed(title="Birthday Bot Manual", description="A list of useful commands", color=0xFF0000)
help_embed.add_field(name=f"{bot.command_prefix}birthday *year* *month* *day*", value="Add your birthday.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}timezone *time_zone*", value="Set your time zone. Make sure to write it just like it's written on the list.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}timezones", value="Get a list of supported time zones.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}hide_age", value="Toggles the appearance of your age in the birthday announcement off.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}show_age", value="Toggles the appearance of your age in the birthday announcement on.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}stats", value="Show the stats for the current server.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}channel *channel_mention*", value="Set the channel in which the birthdays will be announced.", inline=False)
help_embed.set_footer(text="For support: https://discord.gg/u8HNKvr")

async def announce_birthdays():
    await bot.wait_until_ready()
    while not bot.is_closed():
        minute = datetime.datetime.now().minute
        second = datetime.datetime.now().second
        while second != 0 or (minute != 0 and minute != 30 and minute != 45):
            await asyncio.sleep(1)
            minute = datetime.datetime.now().minute
            second = datetime.datetime.now().second
        await asyncio.sleep(1)
        for user in get_users_data():
            user_birthday = user["birth_date"]
            user_time = datetime.datetime.now(tz=pytz.timezone(user["time_zone"]))
            if user_time.hour == 0 and user_time.minute == 0 and user_birthday.month == user_time.month and user_birthday.day == user_time.day:
                for server in get_servers_data():
                    guild = discord.utils.get(bot.guilds, id=server["id"])
                    if guild.get_member(user["id"]) is not None and server["birthday_channel_id"] != None:
                        channel = guild.get_channel(server["birthday_channel_id"])
                        member = guild.get_member(user["id"])
                        if user["hide_age"] == True:
                            try:
                                await channel.send(f"Happy Birthday {member.mention}! :confetti_ball:")
                            except:
                                pass
                        else:
                            age = user_time.year - user_birthday.year
                            try:
                                await channel.send(f"Happy {get_age_with_postfix(age)} Birthday {member.mention}! :confetti_ball:")
                            except:
                                pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id}) | Connected to {len(bot.guilds)} servers | Connected to {len(set(bot.get_all_members()))} users")
    print('--------')
    print('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__, platform.python_version()))
    print('--------')
    print('Use this link to invite {}:'.format(bot.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=335727616'.format(bot.user.id))
    await bot.change_presence(activity=discord.Game(name=f"{get_users_count()} birthdays | type {bot.command_prefix}help"))
    help_embed.set_thumbnail(url=bot.user.avatar_url)
    for guild in bot.guilds:
        if not server_exists(guild.id):
            server_object = {"id" : guild.id, "birthday_channel_id" : None}
            insert_server(server_object)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
    if not server_exists(guild.id):
        server_object = {"id": guild.id, "birthday_channel_id": None}
        insert_server(server_object)

@bot.event
async def on_guild_channel_delete(channel):
    if channel.id == get_bd_channel_id(channel.guild.id):
        if channel.guild.owner.dm_channel == None:
            await channel.guild.owner.create_dm()
        await channel.guild.owner.dm_channel.send(f"The birthday announcement channel in your server **{channel.guild.name}** was deleted.\nPlease set a new announcement channel.")
        update_server(channel.guild.id, {"birthday_channel_id" : None})

@bot.event
async def on_guild_remove(guild):
    remove_server(guild.id)

@bot.command()
async def help(ctx):
    await ctx.send(embed=help_embed)

@bot.command()
async def birthday(ctx, *args):
    if len(args) != 3:
        return await ctx.send(f"Usage: {bot.command_prefix}birthday *year* *month* *day*")
    if all_are_integers(args):
        year, month, day = map(lambda x : int(x), args)  
        if check_date(year, month, day):
            if user_exists(ctx.author.id):
                update_user(ctx.author.id, {"birth_date" : datetime.datetime(year, month, day, 0, 0, 0)})
                return await ctx.send(f"Your birth date has been updated. {ctx.author.mention}")
            user_object = {"id" : ctx.author.id, "birth_date" : datetime.datetime(year, month, day, 0, 0, 0), "time_zone" : "UTC", "hide_age" : False}
            insert_user(user_object)
            await ctx.send(f"Your birthday was added! {ctx.author.mention}\n \
            Make sure to update your time zone with `{bot.command_prefix}timezone`, the default time zone is UTC\n \
            If you don't want your age to appear in the birthday announcement, type `{bot.command_prefix}hide_age`")
            await bot.change_presence(activity=discord.Game(name=f"{get_users_count()} birthdays | type {bot.command_prefix}help"))
        else:
            return await ctx.send("Invalid date.")
    else:
        await ctx.send(f"Usage: {bot.command_prefix}birthday *year* *month* *day*") 

@bot.command()
async def timezone(ctx, *args):
    if not user_exists(ctx.author.id):
        return await ctx.send(f"You must be registered first. Add your birthday with `{bot.command_prefix}birthday`")
    elif len(args) == 0:
        return await ctx.send(f"Usage: {bot.command_prefix}timezone *time_zone*")
    try:
        pytz.timezone(args[0])
        update_user(ctx.author.id, {"time_zone" : args[0]})
        return await ctx.send(f"Your time zone has been updated to `{args[0]}`.")
    except:
        await ctx.send(f"Invalid time zone. Make sure your time zone is written here:\n{timezones_link}")

@bot.command()
async def timezones(ctx):
    await ctx.send(timezones_link)

@bot.command()
async def hide_age(ctx):
    if not user_exists(ctx.author.id):
        return await ctx.send(f"You must be registered first. Add your birthday with `{bot.command_prefix}birthday`")
    update_user(ctx.author.id, {"hide_age" : True})
    await ctx.send(f"Your age will not appear in the birthday announcement.\nTo undo this action, type `{bot.command_prefix}show_age`")

@bot.command()
async def show_age(ctx):
    if not user_exists(ctx.author.id):
        return await ctx.send(f"You must be registered first. Add your birthday with `{bot.command_prefix}birthday`")
    update_user(ctx.author.id, {"hide_age" : False})
    await ctx.send("Your age will appear in the birthday announcement.")

@bot.command()
async def stats(ctx):
    server = get_server_object(ctx.guild.id)
    stats_embed = discord.Embed(title=f"Stats for {ctx.guild.name}", color=0xFF0000)
    birthday_count = 0
    for member in ctx.guild.members:
        if user_exists(member.id):
            birthday_count += 1
    bday_channel = ctx.guild.get_channel(server["birthday_channel_id"])
    channel_name = "(Not set)"
    if bday_channel is not None:
        channel_name = bday_channel.name
    stats_embed.add_field(name="Birthday Count", value=str(birthday_count), inline=False)
    stats_embed.add_field(name="Birthday Announcement Channel", value=channel_name, inline=False)
    await ctx.send(embed=stats_embed)

@bot.command()
async def channel(ctx, *args):
    if len(args) == 0:
        return await ctx.send(f"Usage: {bot.command_prefix}channel *channel_mention*")
    elif not ctx.message.author.guild_permissions.administrator:
        return await ctx.send("You must be an administrator to use this command")
    if is_channel_mention(args[0]):
        ch = ctx.guild.get_channel(int(args[0][2:-1]))
        if ch.is_nsfw() or isinstance(ch, discord.abc.PrivateChannel):
            return await ctx.send("Please select a channel without any restrictions (not private or nsfw).")
        update_server(ctx.guild.id, {"birthday_channel_id" : ch.id})
        return await ctx.send(f"The birthday announcement channel for this server has been updated to `{ch.name}`")
    else:
        await ctx.send("Please mention a channel")

bot.loop.create_task(announce_birthdays())
bot.run(config_data["token"])