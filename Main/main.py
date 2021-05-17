import discord
from os import getenv, listdir, getcwd
from dotenv import load_dotenv

from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import SlashCommandOptionType

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
slash = SlashCommand(bot, override_type = True, sync_commands=True, sync_on_cog_reload=True)

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

@slash.slash(name="load",
            description="Loads a cog", 
            guild_ids=bot.guilds,
            options=[
                create_option(
                    name="cog",
                    description="Specify which cog to load",
                    option_type=SlashCommandOptionType.STRING,
                    required=True,
                    choices=[
                        create_choice(
                            name="Database",
                            value="database"
                        )
                    ]
                )
            ])
async def load(ctx, cog):
    if ctx.author_id in bot.owner_id:
        bot.load_extension(f'cogs.{cog}')
        await ctx.send("Loaded "+cog+" cog")

@bot.command(pass_context=True)
async def unload(ctx, extension):
    if ctx.message.author.id in bot.owner_id:
        bot.unload_extension(f'cogs.{extension}')
        await ctx.send("Unloaded "+extension+" cog")

@bot.command(pass_context=True)
async def reload(ctx, extension):
    if ctx.message.author.id in bot.owner_id:
        bot.reload_extension(f'cogs.{extension}')
        await ctx.send("Reloaded "+extension+" cog")

print(getcwd())
for filename in listdir('cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN, bot=True)
