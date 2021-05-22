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

import re  # regex
import traceback  # for detailed exceptions

import time

load_dotenv()
db = getenv("MONGODB_URI")
guild_ids = [777264818733842442, 828216650473799691, 752331506248056926]


class database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.closest_rem: dict = {}

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
        self.bot.loop.create_task(self.SendRem())
    @commands.command(pass_context=True)
    async def ViewReminder(self, ctx, date, time, timezone, name,):
        mycol = mydb["ID"]
        for x in mycol.find():
            print("Hello");
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
            "channel": ctx.channel.name
        }
        try:
            self.mydb[coll].insert(doc)
            self.Refresh_Closest_Reminder()

            print("\nInserted 1 document into " + coll + " of mydb ")
            print(doc)
            print("\n")

            await ctx.send(
                f'Timezone: {d_aware.tzinfo}\nDay: {d_aware.day}\nMonth: {d_aware.month}\nHour: {d_aware.hour}\nMinute: {d_aware.minute}\n')
        except Exception as e:
            return await ctx.send(e.__str__())

    async def SendRem(self):
        while True:
            present = datetime.utcnow()
            if self.closest_rem != {}:
                if int(present.timestamp() / 60) >= int(self.closest_rem["date_time"].timestamp() / 60):
                    guild = self.bot.get_guild(self.closest_rem["guild_id"])
                    general = discord.utils.find(lambda x: x.name == self.closest_rem['channel'], guild.text_channels)
                    await general.send(f'hi your {self.closest_rem["name"]} reminder is due now!')
                    collection = self.Get_Collection_Name(present)
                    self.mydb[collection].delete_one({'_id': self.closest_rem["_id"]})
                    if self.mydb[collection].count_documents({}) == 0:
                        try:
                            print(f'\tDropped {collection} empty collection')
                            self.mydb.drop_collection(collection)
                        except Exception:
                            traceback.print_exc()
                    self.Refresh_Closest_Reminder()
                else:
                    print('waiting - reminders due')
                    await asyncio.sleep(30)
            else:
                print('waiting - no reminders due')
                await asyncio.sleep(30)

    @commands.command(pass_context=True)
    async def fetch(self, ctx):
        # self.Purge_Expired()
        # self.Refresh_Closest_Reminder()
        if self.closest_rem != {}:
            return await ctx.send(f'Name: {self.closest_rem["name"]}. DateTime: {self.closest_rem["date_time"]}')
        else:
            return await ctx.send(f'No reminders due')


    def Get_Collection_Name(self, datetime: datetime):
        day = f'{datetime.day}'.zfill(2)
        month = f'{datetime.month}'.zfill(2)
        year = f'{datetime.year}'

        return f'{day}-{month}-{year}'

    def Refresh_Closest_Reminder(self):
        print("Getting Earliest Collection: ")
        collections = self.mydb.list_collection_names()
        if not collections:
            self.closest_rem = {}
            return
        earliest_date_obj = datetime.strptime(collections[0], '%d-%m-%Y')

        # Get Earliest Collection
        for collection in collections:
            date_obj = datetime.strptime(collection, '%d-%m-%Y')
            if date_obj < earliest_date_obj:
                earliest_date_obj = date_obj

        earliest_collection = self.Get_Collection_Name(earliest_date_obj)
        print(f'\tEarliest Collection: {earliest_collection}')

        try:
            documents = self.mydb[earliest_collection].find().sort("date_time", 1)
            if documents.count() > 0:
                self.closest_rem = documents[0]
                print(f'\tEarliest Reminder: {documents[0]}')
            else:
                self.closest_rem = {}
        except Exception:
            traceback.print_exc()

    def Purge_Expired(self):
        print("Purging: ")
        present = datetime.utcnow()
        present_collection = self.Get_Collection_Name(present)
        collections = self.mydb.list_collection_names()
        for collection in collections:
            if bool(re.match("^[0-9]{2}-[0-9]{2}-[0-9]{4}$", collection)):
                # Delete expired reminders in present collection
                if collection == present_collection:
                    res = self.mydb[present_collection].delete_many({'date_time': {'$lt': present}})
                    print(f'\tDeleted {res.deleted_count} expired reminders in present collection.')

                # Drop collection if it is empty
                if self.mydb[collection].count_documents({}) == 0:
                    try:
                        print(f'\tDropped {collection} empty collection')
                        self.mydb.drop_collection(collection)
                    except Exception:
                        traceback.print_exc()
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
