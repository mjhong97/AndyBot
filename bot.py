from asyncio import base_events
from multiprocessing.sharedctypes import Value
import posixpath
from turtle import title
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


# @bot.listen()
# async def join(event: hikari.events.member_events.MemberCreateEvent) -> None:
#     channel_id = 986780565049069668
#     await event.app.rest.create_message(channel_id,f"welcome {event.member.mention}!")
    

@bot.command
@lightbulb.command("leaderboard", "view leaderboard")
@lightbulb.implements(lightbulb.PrefixCommand)
async def view_portfolio(ctx):
    query = collections.find({})
    print(query)
    embed = hikari.Embed(
            title= "Leader Board",
            description= "Portfolio value and Total Asset \n The Rankings are based on Total Assets"
        )
    leader_board = []
    total = 0
    for post in query:
        tickers = set(post["portfolio"].items())
        print(len(tickers))
        for each_tickers in tickers:
            ticker, shares = each_tickers
            print(ticker, shares)
            url = "https://finance.yahoo.com/quote/" + ticker + "?p=" + ticker + "&.tsrc=fin-srch"
            price = just_prices(url)
            total += float(price) * shares
            total_assets = post["budget"] + total

        each_user_account = {
            "Name" : post["name"],
            "Portfolio Value" : total,
            "Total Assets" : total_assets
        }
        leader_board.append(each_user_account)
    sorted_leader_board = sorted(leader_board, key=lambda d: d['Total Assets'], reverse = True)
    print(sorted_leader_board)
    count = 0
    for member in sorted_leader_board:
        count += 1
        portfolio_value = "${:,.2f}".format(member["Portfolio Value"])
        total_assets = "${:,.2f}".format(member["Total Assets"])
        embed.add_field(
            name = member["Name"],
            value = "Rank: {} \nPortfolio value : {}  \nTotal Assets: {}".format(count, portfolio_value, total_assets)     
        )
    await ctx.respond(embed)
          
    
    


@bot.command
@lightbulb.command("view", "view portfolio")
@lightbulb.implements(lightbulb.PrefixCommand)
async def view_portfolio(ctx):
    discord_id = ctx.user.id
    discord_username = ctx.user.username
    await ctx.respond(display_account(discord_id, discord_username))

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



def display_account(discord_id, discord_username):                           ### helper function to  view add sell
    query = collections.find_one({"discord_id": discord_id})
    budget_value = query["budget"]
    formatted_budget = "{:,.2f}".format(budget_value)
    total_portfolio_value = 0

    embed = hikari.Embed(
            title= f"{discord_username}'s Account",
            description= "Account Status"
        )
    embed.add_field(
        name="budget",
        value= "$" + formatted_budget
    )    

    value= query["portfolio"]
    if not value:
        embed.add_field(
            name="Portfolio",
            value = "Portfolio is empty"
        )   

    else:
        for company_symbol, number_of_shares in value.items():
            url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
            stock_price = float(just_prices(url)) * number_of_shares
            total_portfolio_value += stock_price
            formatted_price = "${:,.2f}".format(stock_price)
            embed.add_field(
                name = company_symbol,
                value = f"Number of shares: {int(number_of_shares)}\n" + formatted_price 
            )
            embed.edit_field(1, "Portfolio Value", "${:,.2f}".format(total_portfolio_value))
    return embed


@bot.command
@lightbulb.command("buy", "Buy shares of stock if within budget")
@lightbulb.implements(lightbulb.PrefixCommand)
async def buy_stock(ctx):
    try:
        company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !buy AMZN 3
        shares = float(ctx.event.content.split()[2])
    except IndexError:
         await ctx.respond("Please follow example: !buy AMZN 3 ")
    try:
        url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
        stock_price, market_price, market_change = real_time_price(url)
    except ValueError:
        await ctx.respond("That is not a valid ticker symbol.")
    embed = hikari.Embed(title = company_symbol)
    embed.add_field("Stock Price", value=stock_price)
    embed.add_field("Regular Market Price", value=market_price, inline=True)
    embed.add_field("Regular Market Change", value=market_change, inline=True)
    await ctx.respond(embed)
    discord_id = ctx.user.id
    discord_username = ctx.user.username

    await ctx.respond("'Send me a 👍 to confirm'")
    try :
        response = await ctx.bot.wait_for(hikari.MessageEvent, 10000)
        print(f"Buying {shares} of {company_symbol}")

        if str(response.content) == '👍' and response.author_id == discord_id:
            query = collections.find_one({"discord_id": discord_id})
            total = shares * float(stock_price)
            new_budget = query["budget"] - total
            curr_portfolio = query["portfolio"]

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
                print(f"Bought {shares} of {company_symbol}")
    except:
        await ctx.respond("You have timed out. Request to buy again!")


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
    try:
        company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !buy AMZN 3
        shares = float(ctx.event.content.split()[2])
    except IndexError:
         await ctx.respond("Please follow example: !sell AMZN 3 ")

    try:
        url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
        stock_price, market_price, market_change = real_time_price(url)
    except ValueError:
        await ctx.respond("That is not a valid ticker symbol.")
    embed = hikari.Embed(title = company_symbol)
    embed.add_field("Stock Price", value=stock_price)
    embed.add_field("Regular Market Price", value=market_price, inline=True)
    embed.add_field("Regular Market Change", value=market_change, inline=True)
    await ctx.respond(embed)

    discord_id = ctx.user.id
    discord_username = ctx.user.username

    await ctx.respond("'Send me a 👍 to confirm'")
    try:
        response = await ctx.bot.wait_for(hikari.MessageEvent, 10000)

        print(f"Selling {shares} of {company_symbol}")

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
                print(f"Sold {shares} of {company_symbol}")
    except:
        await ctx.respond("You have timed out. Request to buy again!")


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