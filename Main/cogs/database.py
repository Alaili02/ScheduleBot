import asyncio
import json
from time import timezone
import pytz
import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import SlashCommandOptionType
import pymongo
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
import time

load_dotenv()
db = getenv("MONGODB_URI")
guild_ids = [777264818733842442, 828216650473799691, 752331506248056926]


class database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        try:
            self.myclient = pymongo.MongoClient(db, serverSelectionTimeoutMS=2000)
            self.myclient.server_info()
            print(self.myclient.list_database_names())
            self.mydb = self.myclient["myDb"]
            self.mycol = self.mydb["myCollection"]
        except:
            print('Connection To Server Error')

    # @commands.command()
    # async def Connect(self, ctx):
    #     if ctx.message.author.id in self.bot.owner_id:
    #         dblist = self.myclient.list_database_names()
    #         if "myDb" in dblist:
    #             print("The database exists.")                
    #             collist = self.mydb.list_collection_names()
    #             if "myCollection" in collist:
    #                 print("The collection exists.")                    
    #                 mydict = { "name": "Ram", "age": "19", "location": "imagination" }
    #                 x = self.mycol.insert_one(mydict)

    # @commands.command(pass_context=True)
    # async def GetElement(self, ctx):
    #     if ctx.message.author.id in self.bot.owner_id:
    #         mydoc = self.mycol.find_one()
    #         return await ctx.send(mydoc)

    # @commands.command(pass_context=True)
    # async def SetDate(self, ctx,*,arg):
    #     try:
    #         date_time_obj = datetime.strptime(arg, '%d/%m/%y %H:%M')
    #         mydict = { "name": ctx.message.author.name, "date":date_time_obj }
    #         x = self.mycol.insert_one(mydict)
    #         return await ctx.send("date set "+arg)
    #     except:
    #         return await ctx.send("incorrect format please enter dd/mm/yy hh/mm")

    @cog_ext.cog_slash(name="SetReminder",
                       description="testing basic cog slash command",
                       guild_ids=guild_ids,
                       options=[
                           create_option(
                               name="date",
                               description="the day",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                           ),
                           create_option(
                               name="time",
                               description="the time",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                           ),
                           create_option(
                               name="timezone",
                               description="the timezone",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                               choices=[
                                   create_choice(
                                       name="Lebanon/Beirut",
                                       value="Asia/Beirut"
                                   ),
                                   create_choice(
                                       name="Alaili",
                                       value="America/New_York"
                                   ),
                               ]
                           ),
                           create_option(
                               name="name",
                               description="the name",
                               option_type=SlashCommandOptionType.STRING,
                               required=True,
                           ),
                           create_option(
                               name="reminder_description",
                               description="the ReminderDescription",
                               option_type=SlashCommandOptionType.STRING,
                               required=False,
                           ),
                           create_option(
                               name="type_of_reminder",
                               description="the type_of_reminder",
                               option_type=SlashCommandOptionType.STRING,
                               required=False,
                           )
                       ])
    async def SetReminder(self, ctx, date, time, timezone, name, reminder_description='', type_of_reminder=''):
        try:
            date_time_obj = datetime.strptime(date + " " + time, '%d/%m/%y %H:%M')
        except Exception as e:
            return await ctx.send(e.__str__())

        pytz_timezone = pytz.timezone(timezone)
        d_aware = pytz_timezone.localize(date_time_obj)

        utc_date_time = datetime.utcfromtimestamp(d_aware.timestamp())
        present = datetime.utcnow()

        if present < utc_date_time:
            coll_name = f'{utc_date_time.day}-{utc_date_time.month}-{utc_date_time.year}'
            doc = {
                "guild_id": ctx.guild_id,
                "name": name,
                "date_time": utc_date_time,
                "timezone": timezone,
                "reminder_description": reminder_description,
                "type_of_reminder": type_of_reminder
            }
            try:
                mycoll = self.mydb[coll_name].insert(doc)
                print("\nInserted 1 document into " + coll_name + " of mydb ")
                print(json.dumps(doc, indent=4))
                print("\n")
                return await ctx.send(
                    f'Timezone: {d_aware.tzinfo}\nDay: {d_aware.day}\nMonth: {d_aware.month}\nHour: {d_aware.hour}\nMinute: {d_aware.minute}')
            except Exception as e:
                return await ctx.send(e.__str__())
        else:
            return await ctx.send('This date already passed')

    @commands.command(pass_context=True)
    async def SetReminder(self, ctx, date, time, timezone, name, reminder_description='',
                          type_of_reminder=''):
        try:
            date_time_obj = datetime.strptime(date + " " + time, '%d/%m/%y %H:%M')
        except Exception as e:
            return await ctx.send(e.__str__())

        pytz_timezone = pytz.timezone(timezone)
        d_aware = pytz_timezone.localize(date_time_obj)

        utc_date_time = datetime.utcfromtimestamp(d_aware.timestamp())
        present = datetime.utcnow()
        if present < utc_date_time:
            coll_name = f'{utc_date_time.day}-{utc_date_time.month}-{utc_date_time.year}'
            doc = {
                "guild_id": ctx.guild.id,
                "name": name,
                "date_time": utc_date_time,
                "timezone": timezone,
                "reminder_description": reminder_description,
                "type_of_reminder": type_of_reminder,
            }
            try:
                mycoll = self.mydb[coll_name].insert(doc)
                print("\nInserted 1 document into " + coll_name + " of mydb ")
                print(doc)
                print("\n")
                await self.closest_reminder()
                return await ctx.send(
                    f'Timezone: {d_aware.tzinfo}\nDay: {d_aware.day}\nMonth: {d_aware.month}\nHour: {d_aware.hour}\nMinute: {d_aware.minute}')
            except Exception as e:
                return await ctx.send(e.__str__())
        else:
            return await ctx.send('This date already passed')


    async def closest_reminder(self):
        present = datetime.utcnow()
        coll_name = f'{present.day}-{present.month}-{present.year}'
        date = []
        if self.mydb[coll_name].find().count()>0:
            for doc in self.mydb[coll_name].find():
                list1 = [doc['date_time'], doc['name'], doc['guild_id'], doc['_id']]
                # date.append(y['date_time'])
                date.append(list1)
            date.sort()
            print(date[0])
            print(present)
            remaining_date = date[0][0] - present
            print(remaining_date)
            print(remaining_date.total_seconds())
            await asyncio.sleep(remaining_date.total_seconds())
            guild = self.bot.get_guild(date[2])
            general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
            await general.send(f'@everyone your {date[1]} reminder is due now!')
            await self.SendReminder()
        else:
            print('no reminder left')





def setup(bot):
    bot.add_cog(database(bot))
