import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv, listdir, getcwd, execl
import sys
import asyncio
import platform
if platform.system() == 'Windows':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()
TOKEN = getenv("TOKEN")
OWNER_ID1 = getenv("OWNER_ID1")
OWNER_ID2 = getenv("OWNER_ID2")
OWNER_ID3 = getenv("OWNER_ID3")
OWNER_ID4 = getenv("OWNER_ID4")

bot = commands.Bot(
    command_prefix=['rem ', 'Rem '],
    case_insensitive=True,
    owner_id=[int(OWNER_ID1), int(OWNER_ID2), int(OWNER_ID3), int(OWNER_ID4)],
    activity=discord.Activity(name="your schedule", type=discord.ActivityType.watching),
)
guild_ids = [777264818733842442, 828216650473799691, 752331506248056926]

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
    if message.content.lower() == 'bye':
        return await message.channel.send('See ya')
    if message.content.lower() == '':
        return await message.channel.send('')

@bot.command(pass_context=True)
async def load(ctx, cog):
    if ctx.message.author.id in bot.owner_id:
        bot.load_extension(f'cogs.{cog}')
        await ctx.send("Loaded "+cog+" cog")

@bot.command(pass_context=True)
async def unload(ctx, cog):
    if ctx.message.author.id in bot.owner_id:
        bot.unload_extension(f'cogs.{cog}')
        await ctx.send("Unloaded "+cog+" cog")

@bot.command(pass_context=True)
async def reload(ctx, cog):
    if ctx.message.author.id in bot.owner_id:
        bot.reload_extension(f'cogs.{cog}')
        await ctx.send("Reloaded "+cog+" cog")

@bot.command(pass_context=True)
async def restart(ctx):
    if ctx.message.author.id in bot.owner_id:
        await ctx.send("Restarting...")
        await bot.close()
        python = sys.executable
        execl(python, python, * sys.argv)

print(getcwd())
for filename in listdir('./Main/cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN, bot=True)
