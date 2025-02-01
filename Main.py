import discord
from discord.ext import commands
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

# Load bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Folder to store uploaded files
UPLOAD_FOLDER = "uploaded_games"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command to upload the game
@bot.command(name="upload")
async def upload_game(ctx):
    """Handle the upload process."""
    
    if not ctx.message.attachments:
        await ctx.send("⚠️ Please attach a `.rbxl` file to upload!")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith(".rbxl"):
        await ctx.send("❌ Only `.rbxl` files are allowed!")
        return

    file_path = os.path.join(UPLOAD_FOLDER, attachment.filename)
    await attachment.save(file_path)
    
    await ctx.send("Please provide your Roblox cookies to upload the game (send in the format `cookie=value; cookie2=value2`)")

    def check(msg):
        return msg.author == ctx.author and msg.content.startswith('cookie')

    msg = await bot.wait_for("message", check=check)
    roblox_cookies = msg.content.strip()

    await ctx.send("Uploading your game... This may take a while.")
    game_link = await upload_to_roblox(file_path, roblox_cookies)
    
    if game_link:
        await ctx.send(f"✅ Your game has been uploaded! Here's the link: {game_link}")
    else:
        await ctx.send("❌ An error occurred while uploading your game.")

async def upload_to_roblox(file_path, roblox_cookies):
    """Upload the game to Roblox using Selenium and the provided cookies."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://create.roblox.com/")

    cookies = roblox_cookies.split(";")
    for cookie in cookies:
        cookie_parts = cookie.strip().split("=")
        if len(cookie_parts) == 2:
            driver.add_cookie({
                'name': cookie_parts[0].strip(),
                'value': cookie_parts[1].strip(),
                'domain': '.roblox.com'
            })
    
    driver.refresh()
    time.sleep(5)

    try:
        driver.get("https://www.roblox.com/develop/")
        time.sleep(5)
        upload_button = driver.find_element(By.XPATH, '//button[text()="Create New"]')
        upload_button.click()
        time.sleep(3)

        upload_input = driver.find_element(By.XPATH, '//input[@type="file"]')
        upload_input.send_keys(file_path)

        time.sleep(10)

        game_link = driver.current_url
        driver.quit()
        return game_link
    except Exception as e:
        print(f"Error during upload: {e}")
        driver.quit()
        return None

# Run the bot using the token from the environment variable
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: DISCORD_BOT_TOKEN not found. Make sure to set it in your environment variables.")
