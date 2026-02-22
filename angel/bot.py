import discord
from discord.ext import commands
import requests

BOT_OWNER_ID = 1472778356801015913  # your Discord ID
API_URL = "https://angel.onrender.com"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.command()
async def genkey(ctx, days:int=1, usage:int=10):
    if ctx.author.id != BOT_OWNER_ID:
        return await ctx.send("❌ Only owner can use this")
    r = requests.get(f"{API_URL}/generate?days={days}&maxUsage={usage}&owner=angel")
    data = r.json()
    await ctx.send(f"✅ Generated Key:\n`{data['key']}`")

@bot.command()
async def unlimitedkey(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        return await ctx.send("❌ Only owner can use this")
    r = requests.get(f"{API_URL}/generate?unlimited=true&owner=angel")
    data = r.json()
    await ctx.send(f"✅ Unlimited Key:\n`{data['key']}`")

@bot.command()
async def revoke(ctx, key:str):
    if ctx.author.id != BOT_OWNER_ID:
        return await ctx.send("❌ Only owner can use this")
    r = requests.get(f"{API_URL}/revoke?key={key}&owner=angel")
    data = r.json()
    await ctx.send(f"✅ {data['message']}")

bot.run("MTQ3NTA0Njg5NjAxODkxOTYzMQ.G8Gdyx.UMPa7PCrebZ1G_5QUT42yKHyb1I0QOs4Ygu71k")