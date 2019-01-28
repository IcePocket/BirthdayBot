import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import json
import requests
import platform
import datetime
import calendar
import pytz
import re
import dbl
import pymongo

config_path = ""
config_file = open(config_path, "r")
config_data = json.load(config_file)

timezones_link = config_data[""]
db_client = pymongo.MongoClient(config_data[""])
database = db_client[""]
usersCollection = database[""]
serversCollection = database[""]

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

def closest_leap_year(year):
    year += 1
    while not is_leap_year(year):
        year += 1
    return year

def prev_leap_year(year):
    year -= 1
    while not is_leap_year(year):
        year -= 1
    return year

def user_sort_key(user):
    now = datetime.datetime.now()
    date = user["birth_date"]
    if date.month < now.month:
        if date.month == 2 and date.day == 29:
            new_date = datetime.datetime(closest_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year + 1, date.month, date.day, 0, 0, 0)
    elif date.month == now.month and date.day < now.day:
        if date.month == 2 and date.day == 29:
            new_date = datetime.datetime(closest_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year + 1, date.month, date.day, 0, 0, 0)
    else:
        if date.month == 2 and date.day == 29 and not is_leap_year(now.year):
            new_date = datetime.datetime(closest_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year, date.month, date.day, 0, 0, 0)
    delta = new_date - now
    return delta.days

def close_birthday(date):
    now = datetime.datetime.now()
    if date.month < now.month:
        if date.month == 2 and date.day == 29:
            new_date = datetime.datetime(closest_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year + 1, date.month, date.day, 0, 0, 0)
    elif date.month == now.month and date.day < now.day:
        if date.month == 2 and date.day == 29:
            new_date = datetime.datetime(closest_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year + 1, date.month, date.day, 0, 0, 0)
    else:
        if date.month == 2 and date.day == 29 and not is_leap_year(now.year):
            new_date = datetime.datetime(closest_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year, date.month, date.day, 0, 0, 0)
    delta = new_date - now
    return delta.days <= 30

def recent_birthday(date):
    now = datetime.datetime.now()
    if date.month > now.month:
        if date.month == 2 and date.day == 29:
            new_date = datetime.datetime(prev_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year - 1, date.month, date.day, 0, 0, 0)
    elif date.month == now.month and date.day > now.day:
        if date.month == 2 and date.day == 29:
            new_date = datetime.datetime(prev_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year - 1, date.month, date.day, 0, 0, 0)
    else:
        if date.month == 2 and date.day == 29 and not is_leap_year(now.year):
            new_date = datetime.datetime(prev_leap_year(now.year), date.month, date.day, 0, 0, 0)
        else:
            new_date = datetime.datetime(now.year, date.month, date.day, 0, 0, 0)
    delta = now - new_date
    return delta.days <= 30
    
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

def get_number_with_postfix(num):
    num_str = ""
    if num % 10 == 1 and num // 10 != 1:
        num_str = f"{num}st"
    elif num % 10 == 2 and num // 10 != 1:
	    num_str = f"{num}nd"
    elif num % 10 == 3 and num // 10 != 1:
	    num_str = f"{num}rd"
    else:
	    num_str = f"{num}th"
    return num_str

bot = Bot(description="This is a bot whose main purpose is to announce birthdays", command_prefix="~", pm_help = False)
bot.remove_command('help')

help_embed = discord.Embed(title="BirthdayBot", description="Choose a command list.", color=0xFF0000)
help_embed.add_field(name=f"{bot.command_prefix}user_commands", value="Commands that are used to modify your own settings.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}server_commands", value="Commands that are used in servers.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}admin_commands", value="Commands that can be used only by server administrators.", inline=False)
help_embed.add_field(name=f"{bot.command_prefix}info", value="View general info about the bot.", inline=False)
help_embed.set_footer(text="For support: https://discord.gg/u8HNKvr")

user_commands_embed = discord.Embed(title="User Commands", description="Commands that are used to modify your own settings.", color=0xFF0000)
user_commands_embed.add_field(name=f"{bot.command_prefix}birthday *year* *month* *day*", value="Add or update your birthday.", inline=False)
user_commands_embed.add_field(name=f"{bot.command_prefix}timezone *time_zone*", value="Set your time zone. Make sure to write it just like it's written on the list.", inline=False)
user_commands_embed.add_field(name=f"{bot.command_prefix}timezones", value="Get a list of supported time zones.", inline=False)
user_commands_embed.add_field(name=f"{bot.command_prefix}hide_age", value="Toggles the appearance of your age in the birthday announcement off.", inline=False)
user_commands_embed.add_field(name=f"{bot.command_prefix}show_age", value="Toggles the appearance of your age in the birthday announcement on.", inline=False)
user_commands_embed.add_field(name=f"{bot.command_prefix}mention", value="Toggles mentioning yourself in your birthday announcements on/off.", inline=False)

server_commands_embed = discord.Embed(title="Server Commands", description="Commands that are used in servers.", color=0xFF0000)
server_commands_embed.add_field(name=f"{bot.command_prefix}upcoming", value="Check out the upcoming birthdays in the current server.", inline=False)
server_commands_embed.add_field(name=f"{bot.command_prefix}recent", value="Check out the recent birthdays in the current server.", inline=False)
server_commands_embed.add_field(name=f"{bot.command_prefix}birthdays *month*", value="See the birthdays in the given month.", inline=False)
server_commands_embed.add_field(name=f"{bot.command_prefix}stats", value="Show the stats for the current server.", inline=False)

admin_commands_embed = discord.Embed(title="Admin Commands", description="Commands that can be used only by server administrators.", color=0xFF0000)
admin_commands_embed.add_field(name=f"{bot.command_prefix}channel *channel_mention*", value="Set the channel in which the birthdays will be announced.", inline=False)
admin_commands_embed.add_field(name=f"{bot.command_prefix}everyone", value="Toggles mentioning everyone in birthday announcements in the current server on/off.", inline=False)

dblpy = dbl.Client(bot, config_data["dbl_token"])

def get_announcement_text(mention_user, mention_everyone, member_mention):
    if mention_user == True and mention_everyone == True:
        return f"@everyone {member_mention}"
    elif mention_user == True:
        return member_mention
    elif mention_everyone == True:
        return "@everyone "
    else:
        return ""

async def announce_birthdays():
    await bot.wait_until_ready()
    while True:
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
                    if guild is None:
                        continue
                    if guild.get_member(user["id"]) is not None and server["birthday_channel_id"] != None:
                        channel = guild.get_channel(server["birthday_channel_id"])
                        member = guild.get_member(user["id"])
                        if channel is None or member is None:
                            continue
                        try:
                            name = member.name
                            if member.nick is not None:
                                name = member.nick
                            text = get_announcement_text(user["mention"], server["mention_everyone"], member.mention)
                            embed = discord.Embed(title=f"Happy Birthday {name}! :tada:", description="", color=0xFF0000)
                            embed.description += f"{calendar.month_name[user_time.month]} {get_number_with_postfix(user_time.day)}"
                            embed.set_thumbnail(url=member.avatar_url)
                            embed.set_footer(text=str(member))
                            if user["hide_age"] == False:
                                age = user_time.year - user_birthday.year
                                embed.title = f"Happy {get_number_with_postfix(age)} Birthday {name}! :tada:"
                            await channel.send(text, embed=embed)  
                        except:
                            pass

async def post_server_count(bot):
    url = f"https://botsfordiscord.com/api/bot/{bot.user.id}"
    headers = {"Content-Type" : "application/json", "Authorization" : config_data["bfd_token"]}
    data = {"server_count" : len(bot.guilds)}
    requests.post(url=url, headers=headers, data=json.dumps(data))  

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
    user_commands_embed.set_thumbnail(url=bot.user.avatar_url)
    server_commands_embed.set_thumbnail(url=bot.user.avatar_url)
    admin_commands_embed.set_thumbnail(url=bot.user.avatar_url)
    for guild in bot.guilds:
        if not server_exists(guild.id):
            server_object = {"id" : guild.id, "birthday_channel_id" : None, "mention_everyone" : True, "user_ids" : []}
            insert_server(server_object)
    await dblpy.post_server_count()
    await post_server_count(bot)

@bot.event
async def on_message(message):
    if "<@" + str(bot.user.id) + ">" in message.content and not message.author.bot:
        try:
            await message.channel.send(f"type `{bot.command_prefix}help`")
        except:
            pass
    if not message.author.bot:
        await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
    if not server_exists(guild.id):
        server_object = {"id": guild.id, "birthday_channel_id": None, "mention_everyone" : True, "user_ids" : []}
        insert_server(server_object)
        await dblpy.post_server_count()
        await post_server_count(bot)

@bot.event
async def on_guild_channel_delete(channel):
    if channel.id == get_bd_channel_id(channel.guild.id):
        if channel.guild.owner.dm_channel == None:
            await channel.guild.owner.create_dm()
        await channel.guild.owner.dm_channel.send(f"The birthday announcement channel in your server **{channel.guild.name}** was deleted.\nPlease set a new announcement channel.")
        update_server(channel.guild.id, {"birthday_channel_id" : None})

@bot.event
async def on_guild_channel_update(before, after):
    if get_bd_channel_id(after.guild.id) == after.id:
        if after.is_nsfw() or not after.permissions_for(after.guild.get_member(bot.user.id)).send_messages:
            if after.guild.owner.dm_channel == None:
                await after.guild.owner.create_dm()
            await after.guild.owner.dm_channel.send(f"The birthday announcement channel in your server **{after.guild.name}** was updated.\n" + \
            "The update resulted in me not having the permission to send messages to that channel or the channel being marked as NSFW.\n" + \
            "Please set a new announcement channel.")
            update_server(after.guild.id, {"birthday_channel_id" : None})


@bot.event
async def on_guild_remove(guild):
    remove_server(guild.id)
    await dblpy.post_server_count()
    await post_server_count(bot)

@bot.command()
async def help(ctx):
    await ctx.send(embed=help_embed)

@bot.command()
async def user_commands(ctx):
    await ctx.send(embed=user_commands_embed)

@bot.command()
async def server_commands(ctx):
    await ctx.send(embed=server_commands_embed)

@bot.command()
async def admin_commands(ctx):
    await ctx.send(embed=admin_commands_embed)

@bot.command()
async def birthday(ctx, *args):
    if len(args) != 3:
        return await ctx.send(f"Usage: {bot.command_prefix}birthday *year* *month* *day*")
    if all_are_integers(args):
        year, month, day = map(lambda x : int(x), args)  
        if check_date(year, month, day):
            if user_exists(ctx.author.id):
                update_user(ctx.author.id, {"birth_date" : datetime.datetime(year, month, day, 0, 0, 0)})
                embed = discord.Embed(title="Birth date updated.", color=0xFF0000)
                embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
                return await ctx.send(embed=embed)
                
            user_object = {"id" : ctx.author.id, "birth_date" : datetime.datetime(year, month, day, 0, 0, 0), "time_zone" : "UTC", "hide_age" : False, "mention" : True, "server_ids" : []}
            insert_user(user_object)

            embed = discord.Embed(title="Birthday Added!", description="", color=0xFF0000)
            embed.description += f"Use `{bot.command_prefix}timezone` to update your time zone. The default time zone is UTC.\n"
            embed.description += f"Type `{bot.command_prefix}hide_age` if you don't want your age to appear in birthday announcements.\n"
            embed.description += f"Type `{bot.command_prefix}mention` to toggle mentioning yourself in your birthday announcements on/off."
            embed.set_author(name=str(ctx.author))
            embed.set_thumbnail(url=ctx.author.avatar_url)

            await bot.change_presence(activity=discord.Game(name=f"{get_users_count()} birthdays | type {bot.command_prefix}help"))
            await ctx.send(embed=embed)
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
        embed = discord.Embed(title="Time zone updated.", description=f"Your new time zone - {args[0]}", color=0xFF0000)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
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
    embed = discord.Embed(title="Age is now hidden.", description="Your age will not appear in birthday announcements.", color=0xFF0000)
    embed.description += f"\nTo undo this action, type `{bot.command_prefix}show_age`"
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def show_age(ctx):
    if not user_exists(ctx.author.id):
        return await ctx.send(f"You must be registered first. Add your birthday with `{bot.command_prefix}birthday`")
    update_user(ctx.author.id, {"hide_age" : False})
    embed = discord.Embed(title="Age is now visible.", description="Your age will appear in birthday announcements.", color=0xFF0000)
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def mention(ctx):
    if not user_exists(ctx.author.id):
        return await ctx.send(f"You must be registered first. Add your birthday with `{bot.command_prefix}birthday`")
    embed = discord.Embed(title="Mentioning yourself in birthday announcements is now ", description="", color=0xFF0000)
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    user = get_user_object(ctx.author.id)
    if user["mention"] == True:
        embed.title += "**off**."
        embed.description = "The bot will not mention you in your birthday announcements."
        update_user(ctx.author.id, {"mention" : False})
    else:
        embed.title += "**on**."
        embed.description = "The bot will mention you in your birthday announcements."
        update_user(ctx.author.id, {"mention" : True})
    await ctx.send(embed=embed)

@bot.command()
async def upcoming(ctx):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    elif not user_exists(ctx.author.id):
        return await ctx.send(f"If you want to see other people's birthdays, you must add your own! Type `{bot.command_prefix}birthday`")
    embed = discord.Embed(title=f"Upcoming birthdays in {ctx.guild.name}", description="", color=0xFF0000)
    embed.set_thumbnail(url=ctx.guild.icon_url)
    users = []
    for user in get_users_data():
        if ctx.guild.get_member(user["id"]) is not None:
            users.append(user)
    if len(users) == 0:
        embed.description = "No upcoming birthdays."
        return await ctx.send(embed=embed)
    users.sort(key=user_sort_key)
    now = datetime.datetime.now()
    for user in users:
        date = user["birth_date"]
        now = datetime.datetime.now()
        if not close_birthday(date):
            continue
        member = ctx.guild.get_member(user["id"])
        year = datetime.datetime.now().year
        if date.month < now.month:
            year += 1
        name = member.name
        if member.nick is not None:
            name = member.nick
        embed.add_field(name=f"{name} ({member})", value=f"{calendar.month_name[date.month]} {get_number_with_postfix(date.day)}, {year}", inline=False)
    if len(embed.fields) == 0:
        embed.description = "No upcoming birthdays."
    await ctx.send(embed=embed)

@bot.command()
async def recent(ctx):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    elif not user_exists(ctx.author.id):
        return await ctx.send(f"If you want to see other people's birthdays, you must add your own! Type `{bot.command_prefix}birthday`")
    embed = discord.Embed(title=f"Recent birthdays in {ctx.guild.name}", description="", color=0xFF0000)
    embed.set_thumbnail(url=ctx.guild.icon_url)
    users = []
    for user in get_users_data():
        if ctx.guild.get_member(user["id"]) is not None:
            users.append(user)
    if len(users) == 0:
        embed.description = "No recent birthdays."
        return await ctx.send(embed=embed)
    users.sort(key=user_sort_key, reverse=True)
    now = datetime.datetime.now()
    for user in users:
        date = user["birth_date"]
        now = datetime.datetime.now()
        if not recent_birthday(date):
            continue
        member = ctx.guild.get_member(user["id"])
        year = datetime.datetime.now().year
        if date.month > now.month:
            year -= 1
        name = member.name
        if member.nick is not None:
            name = member.nick
        embed.add_field(name=f"{name} ({member})", value=f"{calendar.month_name[date.month]} {get_number_with_postfix(date.day)}, {year}", inline=False)
    if len(embed.fields) == 0:
        embed.description = "No recent birthdays."
    await ctx.send(embed=embed)

@bot.command()
async def birthdays(ctx, *args):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    elif len(args) == 0:
        return await ctx.send(f"Usage: {bot.command_prefix}birthdays *month*")
    elif not user_exists(ctx.author.id):
        return await ctx.send(f"If you want to see other people's birthdays, you must add your own! Type `{bot.command_prefix}birthday`")
    if args[0].title() in list(calendar.month_name):
        month = list(calendar.month_name).index(args[0].title())
    elif args[0].isdigit() and 1 <= int(args[0]) <= 12:
        month = int(args[0])
    else:
        return await ctx.send(f"Invalid month: `{args[0]}`")
    embed = discord.Embed(title=f"{ctx.guild.name} - Birthdays in {calendar.month_name[month]}", description="", color=0xFF0000)
    embed.set_thumbnail(url=ctx.guild.icon_url)
    users = []
    for user in get_users_data():
        if ctx.guild.get_member(user["id"]) is not None and user["birth_date"].month == month:
            users.append(user)
    if len(users) == 0:
        embed.description = f"No birthdays in {calendar.month_name[month]}"
        return await ctx.send(embed=embed) 
    users.sort(key=lambda x : x["birth_date"].day)
    for user in users:
        date = user["birth_date"]
        member = ctx.guild.get_member(user["id"])
        name = member.name
        if member.nick is not None:
            name = member.nick
        embed.add_field(name=f"{name} ({member})", value=f"{calendar.month_name[month]} {get_number_with_postfix(date.day)}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    server = get_server_object(ctx.guild.id)
    stats_embed = discord.Embed(title=f"{ctx.guild.name} - Stats", color=0xFF0000)
    async with ctx.typing():
        birthday_count = 0
        for user in get_users_data():
            if ctx.guild.get_member(user["id"]) is not None:
                birthday_count += 1
        bday_channel = ctx.guild.get_channel(server["birthday_channel_id"])
        channel_name = "N/A"
        if bday_channel is not None:
            channel_name = bday_channel.name
        mention_everyone = server["mention_everyone"]
        stats_embed.add_field(name="Birthday Count", value=str(birthday_count), inline=False)
        stats_embed.add_field(name="Birthday Announcement Channel", value=channel_name, inline=False)
        stats_embed.add_field(name="Mention Everyone", value=str(mention_everyone), inline=False)
        stats_embed.set_thumbnail(url=ctx.guild.icon_url)
    await ctx.send(embed=stats_embed)

@bot.command()
async def channel(ctx, *args):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    if len(args) == 0:
        return await ctx.send(f"Usage: {bot.command_prefix}channel *channel_mention*")
    elif not ctx.message.author.guild_permissions.administrator:
        return await ctx.send("You must be an administrator to use this command.")
    if is_channel_mention(args[0]):
        ch = ctx.guild.get_channel(int(args[0][2:-1]))
        if ch.is_nsfw():
            return await ctx.send("Please select a channel which is not marked as NSFW.")
        elif not ch.permissions_for(ctx.guild.get_member(bot.user.id)).send_messages:
            return await ctx.send("Please select a channel where I can send messages.")
        update_server(ctx.guild.id, {"birthday_channel_id" : ch.id})
        embed = discord.Embed(title="Birthday Announcement Channel Updated.", description="", color=0xFF0000)
        embed.description += f"New birthday announcement channel - {ch.name}"
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_thumbnail(url=bot.user.avatar_url)
        return await ctx.send(embed=embed)
    else:
        await ctx.send("Please mention a channel")

@bot.command()
async def everyone(ctx):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    elif not ctx.message.author.guild_permissions.administrator:
        return await ctx.send("You must be an administrator to use this command.")
    embed = discord.Embed(title="Mentioning everyone in birthday announcements is now ", description="", color=0xFF0000)
    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
    embed.set_thumbnail(url=bot.user.avatar_url)
    server = get_server_object(ctx.guild.id)
    if server["mention_everyone"] == True:
        embed.title += "**off**."
        embed.description = "The bot will not mention everyone in birthday announcements."
        update_server(ctx.guild.id, {"mention_everyone" : False})
    else:
        embed.title += "**on**."
        embed.description = "The bot will mention everyone in birthday announcements."
        update_server(ctx.guild.id, {"mention_everyone" : True})
    await ctx.send(embed=embed)

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="Info", description="General info about the bot", color=0xFF0000)
    embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
    embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Registered Users", value=str(get_users_count()), inline=True)
    embed.add_field(name="Support Server", value="https://discord.gg/u8HNKvr", inline=True)
    embed.add_field(name="Invite Link", value="https://discordapp.com/oauth2/authorize?client_id=490743434773266432&scope=bot&permissions=335727616", inline=False)
    embed.add_field(name="Credits", value="Arik#8773 - Creator, Discord API developer\nMr Doctor Professor Patrick#7943 - Host, MongoDB developer", inline=False)
    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def broadcast(ctx, *args):
    if ctx.guild is not None:
        return
    elif ctx.author.id not in config_data["admin_ids"]:
        return
    elif len(args) == 0:
        return await ctx.send("You must enter a message.")
    msg = " ".join(args)
    embed = discord.Embed(title="Official Administrator Announcement", description=msg, color=0xFF0000)
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    for server in get_servers_data():
        try:
            guild = discord.utils.get(bot.guilds, id=server["id"])
            channel = guild.get_channel(server["birthday_channel_id"])
            if channel is not None:
                await channel.send(embed=embed)
        except:
            pass
    await ctx.send(f"The message was sent.")

bot.loop.create_task(announce_birthdays())
bot.run(config_data["token"])