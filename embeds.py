import discord
import json
import config
import utils

# Getting the data for the embeds
f = open('embeds.json', 'r')
data = f.read()
f.close()

data = data.replace('<PREFIX>', config.prefix())
data = data.replace('<TIMEZONES LINK>', config.timezones_link())
data = data.replace('<SUPPORT LINK>', config.support_link())
embeds = json.loads(data)

# Getting the data for the documentation embeds
f = open('documentation.json', 'r')
documentation_data = f.read()
f.close()

documentation_data = documentation_data.replace('<PREFIX>', config.prefix())
documentation_embeds = json.loads(documentation_data)

# Returns the embed according to the given name
def get_embed(name, color=None): # Returns a discord.Embed object with data from embeds.json according to the given name
    if name not in embeds:
        return None

    embed_dict = embeds[name]
    embed = discord.Embed(title=embed_dict['title'], description=embed_dict['description'], color=color)

    for field in embed_dict['fields']:
        embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    return embed

# Returns the documentation embed of the given command
def get_documentation(command):
    if command not in documentation_embeds:
        return no_documentation(command)

    embed_dict = documentation_embeds[command]
    embed = discord.Embed(title=embed_dict['title'], description=embed_dict['description'], color=config.default_color())

    for field in embed_dict['fields']:
        embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])

    return embed

def birthday_announcement(user, member):
    name = member.display_name
    embed = discord.Embed(title=f'Happy Birthday {name}! :tada:', color=config.default_color())
    embed.description = f'{utils.month_name[user.birthdate.month]} {utils.ordinal_number(user.birthdate.day)}'
    embed.set_author(name=str(member), icon_url=member.avatar_url)
    embed.set_thumbnail(url=member.avatar_url)

    if not user.hidden_age:
        embed.title = f'Happy {utils.ordinal_number(user.age())} Birthday {name}! :tada:'

    return embed

def special_embed(user, user_count):
    embed = discord.Embed(title=f'Congratulations {user}! :tada:', color=config.default_color())
    embed.description = f'You are the {utils.ordinal_number(user_count)} user who added his/her birthday to the bot! '
    embed.description += 'Take a screenshot of this message and become a part of our **Hall of Fame**!\n'
    embed.description += config.special_link()
    embed.set_thumbnail(url=user.avatar_url)
    return embed

def birthday_channel_deleted(server_name):
    embed = discord.Embed(title='Birthday Announcement Channel Deleted', color=config.default_color())
    embed.description = f'The birthday announcement channel in your server **{server_name}** was deleted. '
    embed.description += 'Please set a new announcement channel. '
    embed.description += f'Until you do, birthdays will not be announced in **{server_name}**.'
    return embed

def birthday_channel_updated(server_name, channel_name):
    embed = discord.Embed(title='Invalid Birthday Channel Update', color=config.default_color())
    embed.description = f'The birthday announcement channel **{channel_name}** in your server **{server_name}** was updated. '
    embed.description += 'Now either the channel is NSFW, or I do not have the permission to send messages there. '
    embed.description += 'Please set a new announcement channel. '
    embed.description += f'Until you do, birthdays will not be announced in **{server_name}**.'
    return embed

def birthdays_today(users, guild):
    embed = discord.Embed(title='Birthdays Today', color=config.default_color())
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
    embed.set_thumbnail(url=guild.icon_url)

    for user in users:
        member = guild.get_member(user.id)
        name = member.display_name
        embed.add_field(name=f'**{name}** | _{member}_', value=utils.time_until(utils.tomorrow_midnight(user.local_time())), inline=False)

    if len(embed.fields) == 0:
        embed.description = 'No birthdays right now.'

    return embed

def upcoming_birthdays(users, guild):
    embed = discord.Embed(title='Upcoming Birthdays', color=config.default_color())
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
    embed.set_thumbnail(url=guild.icon_url)

    for user in users:
        member = guild.get_member(user.id)
        name = member.display_name
        date = user.next_birthday()
        embed.add_field(name=f'**{name}** | _{member}_', value=f'{utils.month_name[date.month]} {utils.ordinal_number(date.day)}, {date.year} ({utils.time_until(date)})', inline=False)

    if len(embed.fields) == 0:
        embed.description = 'No upcoming birthdays.'

    return embed

def recent_birthdays(users, guild):
    embed = discord.Embed(title=f'Recent Birthdays', color=config.default_color())
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
    embed.set_thumbnail(url=guild.icon_url)

    for user in users:
        member = guild.get_member(user.id)
        name = member.display_name
        date = user.prev_birthday()
        embed.add_field(name=f'**{name}** | _{member}_', value=f'{utils.month_name[date.month]} {utils.ordinal_number(date.day)}, {date.year}', inline=False)

    if len(embed.fields) == 0:
        embed.description = 'No recent birthdays.'

    return embed

def birthdays_in_month(month, users, guild):
    embed = discord.Embed(title=f'Birthdays in {utils.month_name[month]}', color=config.default_color())
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
    embed.set_thumbnail(url=guild.icon_url)

    for user in users:
        member = guild.get_member(user.id)
        name = member.display_name
        date = user.birthdate
        embed.add_field(name=f'**{name}** | _{member}_', value=f'{utils.month_name[date.month]} {utils.ordinal_number(date.day)}', inline=False)

    if len(embed.fields) == 0:
        embed.description = f'No birthdays in {utils.month_name[month]}.'

    return embed

def stats(bot, server, guild):
    embed = discord.Embed(title=f'Statistics', color=config.default_color())
    embed.set_author(name=guild.name, icon_url=guild.icon_url)
    embed.set_thumbnail(url=guild.icon_url)

    percentage = '%.1f' % (server.birthday_count() / len([member for member in guild.members if not member.bot]) * 100)
    embed.add_field(name='Birthday Count', value=f'{server.birthday_count()} ({percentage}%)')

    embed.add_field(name='Most Birthdays In', value=(server.month_with_most_birthdays() or 'N/A'))
    embed.add_field(name='Average Age', value=('%.1f' % (server.avg_age()) or 'N/A'))

    bot_member_object = guild.get_member(bot.user.id)
    date = str(bot_member_object.joined_at)
    embed.add_field(name='Here Since', value=(date[:date.index('.')] or 'N/A'))

    embed.add_field(name='Mention Everyone', value=str(server.everyone_mentioned))

    announcement_channel = guild.get_channel(server.bday_channel_id)
    embed.add_field(name='Announcement Channel', value=(str(announcement_channel) or 'N/A')) 

    return embed

def info(bot, user_count):
    embed = discord.Embed(title="Info", description="General info about the bot.", color=config.default_color())
    embed.set_thumbnail(url=bot.user.avatar_url)

    embed.add_field(name="Python Version", value=utils.platform.python_version())
    embed.add_field(name="discord.py Version", value=discord.__version__)
    embed.add_field(name="Servers", value=str(len(bot.guilds)))
    embed.add_field(name="Registered Users", value=str(user_count))
    embed.add_field(name="Support Server", value=config.support_link())
    embed.add_field(name="Invite Link", value=config.invite_link(), inline=False)
    embed.add_field(name="Credits", value="Arik#8773 - Creator, Discord API developer\nMr Doctor Professor Patrick#1653 - Host, MongoDB developer", inline=False)

    return embed

def channel_update(new_channel_name):
    embed = discord.Embed(title='Birthday announcement channel updated.', color=config.default_color())
    embed.description = f'New birthday announcement channel: {new_channel_name}'
    return embed

def mention_toggle(mention_bool):
    if mention_bool:
        state = 'on'
        completion = 'will'
    else:
        state = 'off'
        completion = 'will not'

    embed = discord.Embed(title=f'Self mention is now **{state}**.', color=config.default_color())
    embed.description = f'The bot {completion} mention you in your birthday announcements.'
    return embed

def everyone_toggle(everyone_bool):
    if everyone_bool:
        state = 'on'
        completion = 'will'
    else:
        state = 'off'
        completion = 'will not'

    embed = discord.Embed(title=f'Mentioning everyone is now **{state}**.', color=config.default_color())
    embed.description = f'The bot {completion} mention everyone in birthday announcements.'
    return embed

def no_documentation(command):
    embed = discord.Embed(title='Documentation was not found', color=config.default_color())
    embed.description = f'Could not find a documentation of command **{command}**.'
    embed.add_field(name='Possible Causes', value=f'* Command **{command}** does not exist.\n* Command **{command}** does not require parameters.', inline=False)
    return embed

def registration_required(description):
    embed = discord.Embed(title='Registration Required', description=description, color=config.default_color())
    embed.add_field(name='How To Register', value=f'{config.prefix()}birthday <year> <month> <day>', inline=False)
    return embed

def invalid_month(string):
    embed = discord.Embed(title='Invalid Month', color=config.default_color())
    embed.description = f"The value `{string}` is not a valid month. It must be either a number between 1-12 or a month's name."
    return embed