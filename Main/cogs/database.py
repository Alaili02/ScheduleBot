import asyncio
from time import timezone
from dns.name import EmptyLabel
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

import re # regex
import traceback # for detailed exceptions

import time

load_dotenv()
db = getenv("MONGODB_URI")
guild_ids = [777264818733842442, 828216650473799691, 752331506248056926]

class database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.closest_rem: dict

        try:
            self.myclient = pymongo.MongoClient(db, serverSelectionTimeoutMS=2000)
            self.myclient.server_info()
            print(self.myclient.list_database_names())
            self.mydb = self.myclient["myDb"]
            self.mycol = self.mydb["myCollection"]

            self.Purge_Expired()
            self.Refresh_Closest_Reminder()
        except Exception:
            traceback.print_exc()

    @commands.command(pass_context=True)
    async def SetReminder(self, ctx, date, time, timezone, name, reminder_description='', type_of_reminder=''):
        try:
            date_time_obj = datetime.strptime(date + " " + time, '%d/%m/%y %H:%M')
        except Exception as e:
            traceback.print_exc()
            return await ctx.send(e.__str__())

        pytz_timezone = pytz.timezone(timezone)
        d_aware = pytz_timezone.localize(date_time_obj)

        utc_date_time = datetime.utcfromtimestamp(d_aware.timestamp())
        present = datetime.utcnow()
        if present >= utc_date_time:
            return await ctx.send('This date already passed')

        coll = self.Get_Collection_Name(utc_date_time)

        doc = {
            "guild_id": ctx.guild.id,
            "name": name,
            "date_time": utc_date_time,
            "timezone": timezone,
            "reminder_description": reminder_description,
            "type_of_reminder": type_of_reminder,
        }
        try:
            self.mydb[coll].insert(doc)
            self.Refresh_Closest_Reminder()

            print("\nInserted 1 document into " + coll + " of mydb ")
            print(doc)
            print("\n")

            await ctx.send(f'Timezone: {d_aware.tzinfo}\nDay: {d_aware.day}\nMonth: {d_aware.month}\nHour: {d_aware.hour}\nMinute: {d_aware.minute}')
        except Exception as e:
            return await ctx.send(e.__str__())


    async def closest_reminder(self):
        present = datetime.utcnow()
        coll_name = f'{present.day}-{present.month}-{present.year}'
        date = []
        if self.mydb[coll_name].find().count() > 0:
            for doc in self.mydb[coll_name].find():
                list1 = [
                    doc['date_time'], 
                    doc['name'], 
                    doc['guild_id'], 
                    doc['_id']
                ]
                # date.append(y['date_time'])
                date.append(list1)
            date.sort()
            print(date[0])
            print(present)
            remaining_date = date[0][0] - present
            print(remaining_date)
            print(remaining_date.total_seconds())
            await asyncio.sleep(remaining_date.total_seconds())
            guild = self.bot.get_guild(date[0][2])
            general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
            await general.send(f'hi your {date[0][1]} reminder is due now!')
            self.mydb[coll_name].delete_one({'_id': date[0][3]})
            await self.closest_reminder()
        else:
            print('no reminder left')

    @commands.command(pass_context=True)
    async def fetch(self, ctx):
        return await ctx.send(f'Name: {self.closest_rem["name"]}. DateTime: {self.closest_rem["date_time"]}')


    def Get_Collection_Name(self, datetime: datetime):
        day = f'{datetime.day}'.zfill(2)
        month = f'{datetime.month}'.zfill(2)
        year = f'{datetime.year}'
        
        return f'{day}-{month}-{year}'


    def Refresh_Closest_Reminder(self):
        print("Getting Earliest Collection: ")
        collections = self.mydb.list_collection_names()
        earliest_date_obj = datetime.strptime(collections[0], '%d-%m-%Y')

        # Get Earliest Collection
        for collection in collections:
            date_obj = datetime.strptime(collection, '%d-%m-%Y')
            if date_obj < earliest_date_obj:
                earliest_date_obj = date_obj

        earliest_collection = self.Get_Collection_Name(earliest_date_obj)
        print(f'\tEarliest Collection: {earliest_collection}')                     

        try:            
            mydoc = self.mydb[earliest_collection].find().sort("date_time", 1)[0]
            self.closest_rem = mydoc
            print(f'\tEarliest Reminder: {mydoc}')

        except Exception:
            traceback.print_exc()


    def Purge_Expired(self):
        print("Purging: ")
        present = datetime.utcnow()
        present_collection = self.Get_Collection_Name(present)
        collections = self.mydb.list_collection_names()
        for collection in collections:
            if bool(re.match("^[0-9]{2}-[0-9]{2}-[0-9]{4}$", collection)):
                # Drop collection if it is empty
                if self.mydb[collection].count_documents({}) == 0:
                    try:
                        print(f'\tDropped {collection} empty collection')
                        self.mydb.drop_collection(collection)
                    except Exception:
                        traceback.print_exc()
                    continue

                # Delete expired reminders in present collection
                if collection == present_collection:
                    res = self.mydb[present_collection].delete_many({'date_time': {'$lt': present}})
                    print(f'\tDeleted {res.deleted_count} expired reminders in present collection.')
                    continue

                # Valid Collections Continue The Loop Iteration
                day, month, year = collection.split('-')
                if int(year) >= int(present.year):
                    if int(month) >= int(present.month):
                        if int(day) >= int(present.day):
                            continue

                # Expired Collections Are Dropped
                try:
                    print(f'\tDropped {collection} expired collection')
                    self.mydb.drop_collection(collection)
                except Exception:
                    traceback.print_exc()


def setup(bot):
    bot.add_cog(database(bot))


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
