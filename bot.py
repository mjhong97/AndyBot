import hikari
import lightbulb
from nba_champions_dict import *
from real_time_prices import *
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot = lightbulb.BotApp(token = DISCORD_TOKEN, prefix="!")

@bot.listen(hikari.StartedEvent)
async def on_started(event):
    print('Bot has started!')

# Register the command to the bot
@bot.command
# Use the command decorator to convert the function into a command
@lightbulb.command("champions", "Will show score of the finals of chosen year, season mvp, finals mvp")
# Define the command type(s) that this command implements
@lightbulb.implements(lightbulb.PrefixCommand)
async def champions(ctx):   
    #print(dir(ctx.event.content))
    try:
        year = ctx.event.content.split()[1]
        chosen_year = pick_championship_year(int(year))
        await ctx.respond(chosen_year)
    except IndexError:
        await ctx.respond("You must enter a year!")

@bot.command
@lightbulb.command("Prices", "Will show score of the finals of chosen year, season mvp, finals mvp")
@lightbulb.implements(lightbulb.PrefixCommand)
async def champions(ctx):   
    #print(dir(ctx.event.content))
    try:
        company_symbol = ctx.event.content.split()[1].upper()   # Ex input) !see AMZN
        url = "https://finance.yahoo.com/quote/" + company_symbol + "?p=" + company_symbol + "&.tsrc=fin-srch"
        chosen_company = real_time_price(url)
        await ctx.respond(chosen_company)
    except IndexError:
        await ctx.respond("Please enter a valid company symbol!")


    
bot.run()