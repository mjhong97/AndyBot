from asyncio import base_events
import hikari
import lightbulb
from nba_champions_dict import *
from real_time_prices import *
from dotenv import load_dotenv
import os
import pymongo


load_dotenv()
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
MONGO_HOST = os.environ.get("MONGO_HOST")
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD")
MONGO_URL= f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}"

bot = lightbulb.BotApp(token = DISCORD_TOKEN, prefix="!")
client = pymongo.MongoClient(MONGO_URL)

print(type(bot))

#Global variables
db = client["test"]
collections = db["test"]

@bot.listen(hikari.StartedEvent)
async def on_started(event):
    print('Bot has started!')


@bot.command
@lightbulb.command("deleteportfolio", "delete portfolio")
@lightbulb.implements(lightbulb.PrefixCommand)
async def del_portfolio(ctx):

    discord_id = ctx.user.id
    discord_username = ctx.user.username
    query = collections.find_one({"discord_id": discord_id})

    if query == None:
        await ctx.respond("You don't have an existing portfolio!")
    else:
        await ctx.respond(display_account(discord_id, discord_username)) 
        await ctx.respond("Are you sure you want to delete your account?? Type confirm if you are sure")
        response = await ctx.bot.wait_for(hikari.MessageEvent, 10000)
        
        if response.author_id == discord_id and response.message.content.lower() == "confirm":
            collections.delete_one({"discord_id": discord_id})
            await ctx.respond("Your account has been successfully deleted.")    
        # print(dir(response))
        # print(response.author_id)
        # print(response.message.content)
        # print(discord_id)
 



@bot.command
@lightbulb.command("createportfolio", "Create new portfolio")
@lightbulb.implements(lightbulb.PrefixCommand)
async def create_portfolio(ctx):
    # check if user has an existing portofolio
    discord_id = ctx.user.id
    discord_username = ctx.user.username
    query = collections.find_one({"discord_id": discord_id})
    
    if query != None:
        await ctx.respond("You already have an existing portfolio!")
        await ctx.respond(display_account(discord_id, discord_username))    
    
    else:
        new_post = {
            "discord_id" : ctx.user.id,
            "name" : ctx.user.username,
            "budget": 100000,
            "portfolio" : []
        }
        collections.insert_one(new_post)
        
        await ctx.respond("Congratz, you made your paper trading portfolio! Your budget is $100,000.")
        await ctx.respond(display_account(discord_id, discord_username))





def display_account(discord_id, discord_username):                           ### View add sell
    query = collections.find_one({"discord_id": discord_id})
    value= query["portfolio"]
    if not value:
        value = "Portfolio is empty"  
    embed = hikari.Embed(
            title= f"{discord_username}'s Account",
            description= "Account Status"
        )
    embed.add_field(
        name="budget",
        value= query["budget"]
    )    
    embed.add_field(
        name="Portfolio",
        value = value 
    )   
    return embed




@bot.command
@lightbulb.command("prices", "Will show price of chosen ticker/company")
@lightbulb.implements(lightbulb.PrefixCommand)
async def champions(ctx):   
    #print(dir(ctx.event.content))
    try:
        company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !prices AMZN
        url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
        chosen_company = real_time_price(url)
        await ctx.respond(chosen_company)
    except IndexError:
        await ctx.respond("Please enter a valid company symbol!")



# __________________________________________________________________

# Register the command to the bot
@bot.command
# Use the command decorator to convert the function into a command
@lightbulb.command("champions", "Will show score of the finals of chosen year, season mvp, finals mvp")
# Define the command type(s) that this command implements
@lightbulb.implements(lightbulb.PrefixCommand)
async def champions(ctx):   
    # print(dir(ctx))
    try:
        year = ctx.event.content.split()[1]
        chosen_year = pick_championship_year(int(year))
        await ctx.respond(chosen_year)
    except IndexError:
        await ctx.respond("You must enter a year!")
# __________________________________________________________________

    
bot.run()