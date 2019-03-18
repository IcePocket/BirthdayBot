import discord
import asyncio
import config
import database
import embeds
import utils
import validators
import pytz
from datetime import datetime
from discord.ext.commands import Bot
from discord.ext import commands

bot = Bot(command_prefix=config.prefix(), pm_help = False)
bot.remove_command('help')

async def announce_birthdays():
    await bot.wait_until_ready()

    while True:
        now = datetime.now()
        minute = now.minute
        second = now.second

        while second != 0 or minute % 15 != 0:
            await asyncio.sleep(1)
            now = datetime.now()
            minute = now.minute
            second = now.second

        await asyncio.sleep(1)

        for user in database.get_all_users():
            time = user.local_time()

            if time.hour == 0 and time.minute == 0 and user.has_birthday():
                for server in database.get_all_server_objects():
                    guild = discord.utils.get(bot.guilds, id=server['id'])

                    if guild is None:
                        continue

                    channel = guild.get_channel(server['birthday_channel_id'] or 0)
                    member = guild.get_member(user.id)

                    if member is not None and channel is not None:
                        try:
                            embed = embeds.birthday_announcement(user, member)
                            text = utils.get_announcement_text(server['mention_everyone'], user.is_mentioned, member.mention)
                            await channel.send(text, embed=embed)  
                        except:
                            print(f'Sending announcement to server {guild.name} (id: {guild.id}) failed')

@bot.event
async def on_ready():
    utils.clear_screen()
    print(f'Logged in as {bot.user} | Connected to {len(bot.guilds)} servers | Connected to {len(set(bot.get_all_members()))} users')
    print(f'Use this link to invite {bot.user.name}:\n{config.invite_link()}')
    await bot.change_presence(activity=discord.Game(name=f'{database.user_count()} birthdays | type {bot.command_prefix}help'))
    await utils.post_server_count(bot)    
    for guild in bot.guilds:
        if not database.server_exists(guild.id):
            database.insert_server(guild.id, None, True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    message.content = utils.convert_to_command(message.content, '<@' + str(bot.user.id) + '>')
    if message.guild is None and not message.content.startswith(config.prefix()):
        return await message.channel.send(f'type {config.prefix()}help')
    await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
    if not database.server_exists(guild.id):
        database.insert_server(guild.id, None, True)
    await utils.post_server_count(bot)

@bot.event
async def on_guild_channel_delete(channel):
    if channel.id == database.get_birthday_channel_id(channel.guild.id):
        if channel.guild.owner.dm_channel == None:
            await channel.guild.owner.create_dm()
        embed = embeds.birthday_channel_deleted(channel.guild.name)
        await channel.guild.owner.dm_channel.send(embed=embed)
        database.update_birthday_announcement_channel(channel.guild.id, None)

@bot.event
async def on_guild_channel_update(before, after):
    if database.get_birthday_channel_id(after.guild.id) == after.id:
        if after.is_nsfw() or not after.permissions_for(after.guild.get_member(bot.user.id)).send_messages:
            if after.guild.owner.dm_channel == None:
                await after.guild.owner.create_dm()
            embed = embeds.birthday_channel_updated(after.guild.name, after.name)
            await after.guild.owner.dm_channel.send(embed=embed)
            database.update_birthday_announcement_channel(after.guild.id, None)

@bot.event
async def on_guild_remove(guild):
    database.remove_server(guild.id)
    await utils.post_server_count(bot)

@bot.command()
async def help(ctx, *args):
    if len(args) == 0:
        embed = embeds.get_embed('help', config.default_color())
        embed.set_thumbnail(url=bot.user.avatar_url)
        if ctx.guild is not None:
            embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    embed = embeds.get_documentation(args[0])
    text = 'Sent to'

    if args[0] in embed.title:
        embed.set_thumbnail(url=bot.user.avatar_url)
        text = 'Requested by'

    if ctx.guild is not None:
        embed.set_footer(text=f'{text} {ctx.author}', icon_url=ctx.author.avatar_url)
        
    return await ctx.send(embed=embed)

@bot.command()
async def user_commands(ctx):
    embed = embeds.get_embed('user_commands', config.default_color())
    
    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def server_commands(ctx):
    embed = embeds.get_embed('server_commands', config.default_color())

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def admin_commands(ctx):
    embed = embeds.get_embed('admin_commands', config.default_color())

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def other(ctx):
    embed = embeds.get_embed('other_commands', config.default_color())

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def birthday(ctx, *args):
    if len(args) != 3:
        embed = embeds.get_documentation('birthday')
        embed.set_thumbnail(url=bot.user.avatar_url)
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    if not validators.all_are_integers(args):
        embed = embeds.get_embed('invalid_date', config.default_color())
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    year, month, day = map(lambda x : int(x), args)

    if not validators.valid_date(year, month, day):
        embed = embeds.get_embed('invalid_date', config.default_color())
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    if database.user_exists(ctx.author.id):
        database.update_birthday(ctx.author.id, datetime(year, month, day, 0, 0, 0))
        embed = embeds.get_embed('birthday_updated', config.default_color())
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
    
    database.insert_user(ctx.author.id, datetime(year, month, day, 0, 0 ,0), 'UTC', False, True)
    birthday_count = database.user_count()
    await bot.change_presence(activity=discord.Game(name=f'{birthday_count} birthdays | type {bot.command_prefix}help'))

    embed = embeds.get_embed('birthday_added', config.default_color())
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    embed.set_thumbnail(url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

    if birthday_count % 100 == 0:
        embed = embeds.special_embed(ctx.author, birthday_count)
        await ctx.send(embed=embed)

@bot.command()
async def timezone(ctx, *args):
    if not database.user_exists(ctx.author.id):
        embed = embeds.registration_required('In order to set your time zone, you must have a birthday registered in our database first.')
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
    elif len(args) == 0:
        embed = embeds.get_documentation('timezone')
        embed.set_thumbnail(url=bot.user.avatar_url)
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
        
    try:
        pytz.timezone(args[0])
        database.update_timezone(ctx.author.id, args[0])
        embed = embeds.get_embed('timezone_updated', config.default_color())
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
    except:
        embed = embeds.get_embed('invalid_timezone', config.default_color())
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

@bot.command()
async def timezones(ctx):
    embed = embeds.get_embed('timezones', config.default_color())

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)
    
    embed.set_thumbnail(url=bot.user.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def hide_age(ctx):
    if not database.user_exists(ctx.author.id):
        embed = embeds.registration_required('You do not have a birthday registered in our database.')
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
    
    database.hide_age(ctx.author.id)
    embed = embeds.get_embed('age_hidden', config.default_color())
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def show_age(ctx):
    if not database.user_exists(ctx.author.id):
        embed = embeds.registration_required('You do not have a birthday registered in our database.')
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
    
    database.show_age(ctx.author.id)
    embed = embeds.get_embed('age_visible', config.default_color())
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)
    
@bot.command()
async def mention(ctx):
    if not database.user_exists(ctx.author.id):
        embed = embeds.registration_required('You do not have a birthday registered in our database.')
        if ctx.guild is not None:
            embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    embed = embeds.mention_toggle(database.toggle_mention(ctx.author.id))
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def today(ctx):
    if ctx.guild is None:
        return await ctx.send('This command is only available in servers.')
    elif not database.user_exists(ctx.author.id):
        embed = embeds.registration_required("If you want to see other people's birthdays, you must add your own!")
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    async with ctx.typing():
        server = database.get_server(ctx.guild)
        users = server.birthdays_now()
        embed = embeds.birthdays_today(users, ctx.guild)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)    

@bot.command()
async def upcoming(ctx):
    if ctx.guild is None:
        return await ctx.send('This command is only available in servers.')
    elif not database.user_exists(ctx.author.id):
        embed = embeds.registration_required("If you want to see other people's birthdays, you must add your own!")
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    async with ctx.typing():
        server = database.get_server(ctx.guild)
        users = server.upcoming_birthdays()
        embed = embeds.upcoming_birthdays(users, ctx.guild)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)
    
    await ctx.send(embed=embed)

@bot.command()
async def recent(ctx):
    if ctx.guild is None:
        return await ctx.send('This command is only available in servers.')
    elif not database.user_exists(ctx.author.id):
        embed = embeds.registration_required("If you want to see other people's birthdays, you must add your own!")
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    async with ctx.typing():
        server = database.get_server(ctx.guild)
        users = server.recent_birthdays()
        embed = embeds.recent_birthdays(users, ctx.guild)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)
    
    await ctx.send(embed=embed)

@bot.command()
async def birthdays(ctx, *args):
    if ctx.guild is None:
        return await ctx.send("This command is only available in servers.")
    elif not database.user_exists(ctx.author.id):
        embed = embeds.registration_required("If you want to see other people's birthdays, you must add your own!")
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)
    elif len(args) == 0:
        embed = embeds.get_documentation('birthdays')
        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    month = utils.convert_month_to_number(args[0])

    if month is None:
        embed = embeds.invalid_month(args[0])
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    async with ctx.typing():
        server = database.get_server(ctx.guild)
        users = server.birthdays_in_month(month)
        embed = embeds.birthdays_in_month(month, users, ctx.guild)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)
    
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx):
    if ctx.guild is None:
        return await ctx.send('This command is only available in servers.')

    async with ctx.typing():
        server = database.get_server(ctx.guild)
        embed = embeds.stats(bot, server, ctx.guild)
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

@bot.command()
async def channel(ctx, *args):
    if ctx.guild is None:
        return await ctx.send('This command is only available in servers.')
    elif not ctx.message.author.guild_permissions.administrator:
        return await ctx.send('You must be an administrator to use this command.')
    elif len(args) == 0 or not validators.channel_mention(args[0]):
        embed = embeds.get_documentation('channel')
        embed.set_thumbnail(url=bot.user.avatar_url)
        embed.set_footer(text=f'Sent to {ctx.author}', icon_url=ctx.author.avatar_url)
        return await ctx.send(embed=embed)

    channel = ctx.guild.get_channel(int(args[0][2:-1]))

    if channel is None:
        return await ctx.send('Could not find the specified channel.')
    elif channel.is_nsfw():
        return await ctx.send('Please select a channel which is not marked as NSFW.')
    elif not channel.permissions_for(ctx.guild.get_member(bot.user.id)).send_messages:
        return await ctx.send("Please select a channel where I can send messages.")
    
    database.update_birthday_announcement_channel(ctx.guild.id, channel.id)
    
    embed = embeds.channel_update(channel.name)
    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
    embed.set_footer(text=f'Modified by {ctx.author}', icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def everyone(ctx):
    if ctx.guild is None:
        return await ctx.send('This command is only available in servers.')
    elif not ctx.message.author.guild_permissions.administrator:
        return await ctx.send('You must be an administrator to use this command.')

    embed = embeds.everyone_toggle(database.toggle_everyone(ctx.guild.id))
    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
    embed.set_footer(text=f'Modified by {ctx.author}', icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

@bot.command()
async def vote(ctx):
    embed = embeds.get_embed('vote', config.default_color())
    embed.set_thumbnail(url=bot.user.avatar_url)

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

@bot.command()
async def support(ctx):
    embed = embeds.get_embed('support', config.default_color())
    embed.set_thumbnail(url=bot.user.avatar_url)

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

@bot.command()
async def info(ctx):
    embed = embeds.info(bot, database.user_count())

    if ctx.guild is not None:
        embed.set_footer(text=f'Requested by {ctx.author}', icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

@bot.command()
async def broadcast(ctx, *args):
    if ctx.guild is not None or ctx.author.id not in config.admin_ids():
        return
    elif len(args) == 0:
        return await ctx.send('You must enter a message.')

    msg = ' '.join(args)
    embed = discord.Embed(title='Official Administrator Announcement', description=msg, color=config.default_color())
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)

    for server in database.get_all_server_objects():
        try:
            guild = discord.utils.get(bot.guilds, id=server["id"])
            channel = guild.get_channel(server["birthday_channel_id"])
            if channel is not None:
                await channel.send(embed=embed)
        except:
            pass
    await ctx.send(f"The message was sent.")

bot.loop.create_task(announce_birthdays())
bot.run(config.token())