import discord
import requests
import validators
import config
import json
import platform
import datetime
from datetime import datetime, timedelta
from calendar import month_name
from re import search
from os import system

# Utility functions

def ordinal_number(n):
    if n % 10 == 1 and n // 10 != 1:
        num = f"{n}st"
    elif n % 10 == 2 and n // 10 != 1:
	    num = f"{n}nd"
    elif n % 10 == 3 and n // 10 != 1:
	    num = f"{n}rd"
    else:
	    num = f"{n}th"
    return num

def clear_screen():
    if platform.system() == 'Linux':
        system('clear')
    elif platform.system() == 'Windows':
        system('cls')
    else:
        raise Exception('Function "clear_screen" works only on Linux/Windows')

# Returns the closest leap year to the given year (including the given year)
def closest_leap_year(year):
    if validators.leap_year(year):
        return year
    
    while not validators.leap_year(year):
        year += 1

    return year

# Returns the closest leap year to the given year (excluding the given year)
def closest_next_leap_year(year):
    year += 1
    
    while not validators.leap_year(year):
        year += 1

    return year

# Returns the last leap year (could be the given year)
def last_leap_year(year):
    if validators.leap_year(year):
        return year

    while not validators.leap_year(year):
        year -= 1

    return year

# Returns the last leap year prior to the given year
def last_prev_leap_year(year):
    year -= 1

    while not validators.leap_year(year):
        year -= 1

    return year

# Returns the necessary mentions for the announcement in a string
def get_announcement_text(mention_everyone, mention_user, member_mention):
    if mention_everyone and mention_user:
        return f'@everyone {member_mention}'
    elif mention_everyone:
        return '@everyone'
    elif mention_user:
        return member_mention
    return ''

# Returns the given month (in any format) as a number
def convert_month_to_number(month_str):
    if month_str.title() in list(month_name):
        return list(month_name).index(month_str.title())
    elif month_str.title() in [month[:3] for month in list(month_name)]:
        return [month[:3] for month in list(month_name)].index(month_str.title())
    elif month_str.isdigit() and 1 <= int(month_str) <= 12:
        return int(month_str)
    return None

# Returns the amount of mutual servers between the bot and a user
def mutual_server_count(bot, user_id):
    count = 0

    for guild in bot.guilds:
        if guild.get_member(user_id) is not None:
            count += 1

    return count

def convert_to_command(s, bot_mention):
    if s == bot_mention: # If the message mentions the bot
        return config.prefix() + 'help'
    elif s.startswith(bot_mention): # Accepts the bot's mention as the command prefix
        s = s.replace(bot_mention, config.prefix())
        if len(s) > 1 and s[1] == ' ':
            s = s.replace(' ', '', 1)
    return s
 
# Posts the bot's server count to every website it's listed on
async def post_server_count(bot):
    # Posting to Discord Bot List
    dbl_url = f'https://discordbots.org/api/bots/{bot.user.id}/stats'
    dbl_headers = {'Authorization' : config.dbl_token()}
    dbl_data = {'server_count' : len(bot.guilds)}
    requests.post(dbl_url, headers=dbl_headers, data=json.dumps(dbl_data))

    # Posting to Bots For Discord
    bfd_url = f'https://botsfordiscord.com/api/bot/{bot.user.id}'
    bfd_headers = {'Content-Type' : 'application/json', 'Authorization' : config.bfd_token()}
    bfd_data = {'server_count' : len(bot.guilds)}
    requests.post(url=bfd_url, headers=bfd_headers, data=json.dumps(bfd_data))

def time_until(date):
    now = datetime.now(tz=date.tzinfo)

    if date < now:
        return None

    delta = date - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if days >= 2:
        message = f'{days} days left'
    elif days == 1:
        message = f'1 day, {hours} hour(s) left'
    elif hours >= 2:
        message = f'{hours} hours left'
    elif hours == 1:
        message = f'1 hour, {minutes} minute(s) left'
    elif minutes >= 2:
        message = f'{minutes} minutes left'
    elif minutes == 1:
        message = f'1 minute left'
    else:
        message = 'less than a minute left'

    return message

def tomorrow_midnight(date):
    tomorrow = date + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, tzinfo=date.tzinfo)