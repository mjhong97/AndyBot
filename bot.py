import hikari
import lightbulb

bot = lightbulb.BotApp(token='OTg2MDA3NDIyOTc4MTEzNTQ2.Gb8uAu.MAJNnhVIMxPAYxSHV3jvRt7Z1NGOKMDuN4dNPs', prefix="!")

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
    print("working!")
    print(dir(ctx.event.content))
    try:
        year = ctx.event.content.split()[1]
        await ctx.respond(year)
    except IndexError:
        await ctx.respond("You must enter a year!")
bot.run()