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
            "budget": 100000.00,
            "portfolio" : {}
        }
        collections.insert_one(new_post)
        
        await ctx.respond("Congratz, you made your paper trading portfolio! Your budget is $100,000.")
        await ctx.respond(display_account(discord_id, discord_username))





def display_account(discord_id, discord_username):                           ### View add sell
    query = collections.find_one({"discord_id": discord_id})
    budget_value = query["budget"]
    formatted_budget = "{:,.2f}".format(budget_value)

    value= query["portfolio"]
    if not value:
        value = "Portfolio is empty"

    embed = hikari.Embed(
            title= f"{discord_username}'s Account",
            description= "Account Status"
        )
    embed.add_field(
        name="budget",
        value= "$" + formatted_budget
    )    
    embed.add_field(
        name="Portfolio",
        value = value
    )   
    return embed

# add buy, sell, view to group command
# buy and sell can have option commands
@bot.command
@lightbulb.command("buy", "Buy shares of stock if within budget")
@lightbulb.implements(lightbulb.PrefixCommand)
async def buy_stock(ctx):
    company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !buy AMZN 3
    shares = float(ctx.event.content.split()[2])
    url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
    stock_price, market_price, market_change = real_time_price(url)
    
    embed = hikari.Embed(title = company_symbol)
    embed.add_field("Stock Price", value=stock_price)
    embed.add_field("Regular Market Price", value=market_price, inline=True)
    embed.add_field("Regular Market Change", value=market_change, inline=True)
    await ctx.respond(embed)
    discord_id = ctx.user.id
    discord_username = ctx.user.username

    await ctx.respond("'Send me a 👍 to confirm'")
    response = await ctx.bot.wait_for(hikari.MessageEvent, 10000)

    if str(response.content) == '👍' and response.author_id == discord_id:
        query = collections.find_one({"discord_id": discord_id})
        print(query)
        total = shares * float(stock_price)
        new_budget = query["budget"] - total
        curr_portfolio = query["portfolio"]
        print(curr_portfolio)
        print(type(curr_portfolio))
        if query == None:
            await ctx.respond("You don't have an existing portfolio!")
        elif query["budget"] < total:
            await ctx.respond("You don't have enough money..")
        else:
            updated_portfolio = buy_and_update_portfolio(curr_portfolio, company_symbol, shares)
            to_update = {
                "budget" : new_budget,
                "portfolio" : updated_portfolio
            }
            collections.update_one({"discord_id" : discord_id}, {"$set":to_update})
            await ctx.respond(display_account(discord_id, discord_username))
         
# Timer for the buy function - we should implement
    # try:
    #     response = await ctx.bot.wait_for(hikari.MessageEvent, 10000)
    #     if str(response.content) == '👍':
    # except:
    #     await ctx.respond("You have timed out. Request to buy again!")


def buy_and_update_portfolio(curr_portfolio, ticker, shares):
    # curr_portfolio is a dict where ticker is key and shares is value
    # if ticker is in dict then increment shares
    # else we add to portfolio
    if ticker in curr_portfolio:
        curr_portfolio[ticker] += shares
    else:
        curr_portfolio[ticker] = shares
    
    return curr_portfolio


@bot.command
@lightbulb.command("sell", "Sell shares of stock if within budget")
@lightbulb.implements(lightbulb.PrefixCommand)
async def sell_stock(ctx):
    company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !buy AMZN 3
    shares = float(ctx.event.content.split()[2])
    url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
    stock_price, market_price, market_change = real_time_price(url)
    
    embed = hikari.Embed(title = company_symbol)
    embed.add_field("Stock Price", value=stock_price)
    embed.add_field("Regular Market Price", value=market_price, inline=True)
    embed.add_field("Regular Market Change", value=market_change, inline=True)
    await ctx.respond(embed)

    discord_id = ctx.user.id
    discord_username = ctx.user.username

    await ctx.respond("'Send me a 👍 to confirm'")
    response = await ctx.bot.wait_for(hikari.MessageEvent, 10000)

    if str(response.content) == '👍' and response.author_id == discord_id:
        query = collections.find_one({"discord_id": discord_id})
    
        total = shares * float(stock_price)
        new_budget = query["budget"] + total
        curr_portfolio = query["portfolio"]

        if query == None:
            await ctx.respond("You don't have an existing portfolio!")
        elif shares > curr_portfolio[company_symbol]:
            await ctx.respond("Not enough shares to sell")
        else:
            updated_portfolio = sell_and_update_portfolio(curr_portfolio, company_symbol, shares)
            to_update = {
                "budget" : new_budget,
                "portfolio" : updated_portfolio
            }
            collections.update_one({"discord_id" : discord_id}, {"$set":to_update})
            await ctx.respond(display_account(discord_id, discord_username))


def sell_and_update_portfolio(curr_portfolio, ticker, shares):
    # curr_portfolio is a dict where ticker is key and shares is value
    # if ticker is in dict then increment shares
    # else we add to portfolio
    if ticker in curr_portfolio:
            curr_portfolio[ticker] -= shares
    
    return curr_portfolio


@bot.command
@lightbulb.command("prices", "Will show price of chosen ticker/company")
@lightbulb.implements(lightbulb.PrefixCommand)
async def champions(ctx):   
    #print(dir(ctx.event.content))
    try:
        company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !prices AMZN
        url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
        stock_price, market_price, market_change = real_time_price(url)
        embed = hikari.Embed(title = company_symbol)
        embed.add_field("Stock Price", value=stock_price)
        embed.add_field("Regular Market Price", value=market_price, inline=True)
        embed.add_field("Regular Market Change", value=market_change, inline=True)
        await ctx.respond(embed)
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