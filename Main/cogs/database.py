import discord
from discord.ext import commands
import pymongo


class database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.myclient = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS = 2000)
            self.myclient.server_info()
            print(self.myclient.list_database_names())
        except:
            print('Connection To Server Error')


    @commands.command()
    async def Connect(self, ctx):
        if ctx.message.author.id in self.bot.owner_id:
            dblist = self.myclient.list_database_names()
            if "myDb" in dblist:
                print("The database exists.")
                mydb = self.myclient["myDb"]
                collist = mydb.list_collection_names()
                if "myCollection" in collist:
                    print("The collection exists.")
                    mycol = mydb["myCollection"]
                    mydict = { "name": "Ram", "age": "17", "location": "imagination" }
                    x = mycol.insert_one(mydict)

    
    @commands.command(pass_context=True)
    async def GetRam(self, ctx):
        if ctx.message.author.id in self.bot.owner_id:
            myDb =  self.myclient["myDb"]
            myColl = myDb["myCollection"]
            mydoc = myColl.find_one({"name": "Ram"})
            return await ctx.send(mydoc['age'])

def setup(bot):
    bot.add_cog(database(bot))