import asyncio
from os import getenv, listdir, getcwd, execl
from time import timezone
from pymongo.common import MAX_SUPPORTED_WIRE_VERSION
import pytz
import discord
from discord.ext import commands
import pymongo
from dotenv import load_dotenv
from os import getenv
from datetime import datetime

import re  # regex
import traceback  # for detailed exceptions

from bson.objectid import ObjectId

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
    async def GetTimezones(self,ctx):
        print(getcwd())
        return await ctx.send(file=discord.File(r'Main/timezones.txt'))


    @commands.command(pass_context=True)
    async def ViewReminder(self,ctx):
        reminders = self.getReminders(ctx.guild.id)
        if (len(reminders) == 0):
            return await ctx.send("No reminders!")
        await ctx.send("Reminders: ")
        for reminder in reminders:
            await ctx.send('\t' + reminder['message'])

    @commands.command(pass_context=True)
    async def DeleteReminder(self,ctx):
        reminders = self.getReminders(ctx.guild.id)
        if (len(reminders) == 0):
            return await ctx.send("No reminders to delete!")
        await ctx.send("Reply the index of the reminder that you wish to delete: ")
        for reminder in reminders:
            await ctx.send('\t' + reminder['message'])

        def check(m):
            if m.channel == ctx.channel:
                if m.author == ctx.message.author:
                    try:
                        int(m.content)
                        return True
                    except ValueError:
                        return False
            return False

        is_valid_index = False
        while not is_valid_index:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=20.0)
            except asyncio.exceptions.TimeoutError:
                await ctx.send("Timed out!")
                return

            index = int(msg.content) - 1
            if 0 <= index <= len(reminders):
                is_valid_index = True
            else:
                await ctx.send("Please pick a valid message number")


        collection = reminders[index]['collection']
        _id = reminders[index]['_id']

        try:
            self.mydb[collection].delete_one({'_id': ObjectId(_id)})
            self.Refresh_Closest_Reminder()
            return await ctx.send("Deleted " + reminders[index]['name'] + " reminder.")
        except Exception:
            return await ctx.send("Failed")

    def getReminders(self, guild_id):
        collections = self.mydb.list_collection_names()
        count = 1
        reminders_returned = []

        for collection in collections:
            if bool(re.match("^[0-9]{2}-[0-9]{2}-[0-9]{4}$", collection)):
                documents = self.mydb[collection].find()
                for x in documents:
                    if  x['guild_id'] == guild_id:

                        pytz_timezone = pytz.timezone(x['timezone'])
                        date_time_obj = x['date_time']

                        d_aware = pytz.utc.localize(date_time_obj)
                        d_converted = d_aware.astimezone(pytz_timezone)

                        if x["reminder_description"]:
                            message = f'{count} - {d_converted} - {x["timezone"]} - {x["name"]} - {x["reminder_description"]}'
                        else:
                            message = f'{count} - {d_converted} - {x["timezone"]} - {x["name"]}'

                        reminders_returned.append({ 
                            'collection': collection, 
                            '_id': x['_id'],
                            'message': message,
                            'name': x["name"]
                        })   
                        count += 1
        return reminders_returned
        
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

            print("\nInserted 1 document into " + coll + " of mydb ")
            print(doc)
            print("\n")

            self.Refresh_Closest_Reminder()

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
                    print('Waiting - Reminders due')
                    await asyncio.sleep(30)
            else:
                print('Waiting - No reminders due')
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
        print("Getting Earliest Reminder: ")
        collections = self.mydb.list_collection_names()
        if not collections:
            self.closest_rem = {}
            return

        # Get Earliest Collection
        earliest_date_obj = datetime.strptime(collections[0], '%d-%m-%Y')
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
        # Remove the hours, minutes, seconds from present date time
        present_date_obj = datetime.strptime(present_collection, '%d-%m-%Y')

        collections = self.mydb.list_collection_names()

        print(f'Present date: \t{present_date_obj}')

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
                collection_date_obj = datetime.strptime(collection, '%d-%m-%Y')
                print(f'Collection Date: \t{collection_date_obj}')
                print(f'\tValid: \t{collection_date_obj >= present_date_obj}')
                if collection_date_obj >= present_date_obj:
                    continue

                # Expired Collections Are Dropped
                try:
                    print(f'\tDropped {collection} expired collection')
                    self.mydb.drop_collection(collection)
                except Exception:
                    traceback.print_exc()


def setup(bot):
    bot.add_cog(database(bot))
