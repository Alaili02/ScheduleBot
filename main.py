import discord
from os import getenv
from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = getenv("TOKEN")
OWNER_ID1 = getenv("OWNER_ID1")
OWNER_ID2 = getenv("OWNER_ID2")

bot = commands.Bot(
    command_prefix='*',
    case_insensitive=True,
    owner_id=[int(OWNER_ID1), int(OWNER_ID2)],
    activity=discord.Activity(name="your schedule", type=discord.ActivityType.watching),
)
bot.remove_command('help')

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
    elif 'hello' in message.content.lower():
        return await message.channel.send('Hello')

bot.run(TOKEN, bot=True)
