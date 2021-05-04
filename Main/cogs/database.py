import discord
from discord.ext import commands
import pymongo
from dotenv import load_dotenv
from os import getenv
load_dotenv()
db= getenv("MONGODB_URI")

class database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        try: 
            
            self.myclient = pymongo.MongoClient(db, serverSelectionTimeoutMS = 2000)
            self.myclient.server_info()
            print(self.myclient.list_database_names())
            self.mydb = self.myclient["myDb"]
            self.mycol = self.mydb["myCollection"]
        except:
            print('Connection To Server Error')


    @commands.command()
    async def Connect(self, ctx):
        if ctx.message.author.id in self.bot.owner_id:
            dblist = self.myclient.list_database_names()
            if "myDb" in dblist:
                print("The database exists.")                
                collist = self.mydb.list_collection_names()
                if "myCollection" in collist:
                    print("The collection exists.")                    
                    mydict = { "name": "Ram", "age": "17", "location": "imagination" }
                    x = self.mycol.insert_one(mydict)

    
    @commands.command(pass_context=True)
    async def GetElement(self, ctx):
        if ctx.message.author.id in self.bot.owner_id:
            mydoc = self.mycol.find_one({"name": "Ram"})
            return await ctx.send(mydoc['age'])
    @commands.command(pass_context=True)
    async def SetDate(self, ctx,*,arg):
        return await ctx.send(arg)
        


def setup(bot):
    bot.add_cog(database(bot))