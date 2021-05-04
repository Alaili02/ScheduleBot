import discord
from os import getenv, listdir
from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = getenv("TOKEN")
OWNER_ID1 = getenv("OWNER_ID1")
OWNER_ID2 = getenv("OWNER_ID2")
OWNER_ID3 = getenv("OWNER_ID3")
OWNER_ID4 = getenv("OWNER_ID4")

bot = commands.Bot(
    command_prefix='*',
    case_insensitive=True,
    owner_id=[int(OWNER_ID1), int(OWNER_ID2), int(OWNER_ID3), int(OWNER_ID4)],
    activity=discord.Activity(name="your schedule", type=discord.ActivityType.watching),
)

@bot.event
async def on_ready():
    print('I have logged in as {0.user.name}'.format(bot))
    for guild in bot.guilds:
        general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
        if general and general.permissions_for(guild.me).send_messages:
            print("Joined " + general.name)


@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == 'hi':
        return await message.channel.send('Hello')
    elif "rem" in message.content.lower():
        print("hello console")
        return await message.channel.send('baka shinaide kudasai')
    elif "set date" in message.content.lower():
        return await message.channel.send('ded')

@bot.command(pass_context=True)
async def load(ctx, extension):
    if ctx.message.author.id in bot.owner_id:
        bot.load_extension(f'cogs.{extension}')
        await ctx.send("Loaded "+extension+" cog")

@bot.command(pass_context=True)
async def unload(ctx, extension):
    if ctx.message.author.id in bot.owner_id:
        bot.unload_extension(f'cogs.{extension}')
        await ctx.send("Unloaded "+extension+" cog")

@bot.command(pass_context=True)
async def reload(ctx, extension):
    if ctx.message.author.id in bot.owner_id:
        bot.unload_extension(f'cogs.{extension}')
        bot.load_extension(f'cogs.{extension}')
        await ctx.send("Reloaded "+extension+" cog")


for filename in listdir('cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN, bot=True)
