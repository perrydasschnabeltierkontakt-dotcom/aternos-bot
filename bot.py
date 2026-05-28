import asyncio
import json
import os
import sys
import shutil
import traceback

import discord
from discord import Embed
from discord import app_commands
from dotenv import load_dotenv
from pyppeteer import launch

load_dotenv()

CONFIG_PATH = 'config.json'
config = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as error:
        print('Fehler beim Laden von config.json:', error)
        sys.exit(1)

TOKEN = os.getenv('DISCORD_TOKEN') or config.get('DISCORD_TOKEN')
CLIENT_ID = os.getenv('DISCORD_CLIENT_ID') or config.get('DISCORD_CLIENT_ID')
GUILD_ID = os.getenv('DISCORD_GUILD_ID') or config.get('DISCORD_GUILD_ID')
ATERNOS_LOGIN = os.getenv('ATERNOS_LOGIN') or config.get('ATERNOS_LOGIN') or os.getenv('ATERNOS_EMAIL') or config.get('ATERNOS_EMAIL')
ATERNOS_PASSWORD = os.getenv('ATERNOS_PASSWORD') or config.get('ATERNOS_PASSWORD')
ATERNOS_SERVER_URL = os.getenv('ATERNOS_SERVER_URL') or config.get('ATERNOS_SERVER_URL') or 'https://aternos.org/server'

if not TOKEN or not CLIENT_ID or not GUILD_ID:
    print('Bitte setze DISCORD_TOKEN, DISCORD_CLIENT_ID und DISCORD_GUILD_ID in config.json oder als Umgebungsvariablen.')
    sys.exit(1)

if not ATERNOS_LOGIN or not ATERNOS_PASSWORD:
    print('Bitte setze ATERNOS_LOGIN (oder ATERNOS_EMAIL) und ATERNOS_PASSWORD in config.json oder als Umgebungsvariablen.')
    sys.exit(1)

intents = discord.Intents.none()
intents.guilds = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def create_embed(title: str, description: str, color: int) -> Embed:
    return Embed(title=title, description=description, color=color)


async def find_button(page, patterns):
    elements = await page.querySelectorAll('button, a, input[type=button], input[type=submit]')
    for element in elements:
        text = await page.evaluate('(element) => element.innerText || element.value || ""', element)
        if not text:
            continue
        normalized = text.strip().lower()
        for pattern in patterns:
            if pattern.lower() in normalized:
                return element
    return None


async def start_aternos_server():
    def find_chrome_executable():
        # check common env vars first
        # allow specifying path in config.json as well
        cfg_path = config.get('PUPPETEER_EXECUTABLE_PATH')
        if cfg_path:
            return cfg_path

        for name in ('PUPPETEER_EXECUTABLE_PATH', 'CHROME_PATH', 'GOOGLE_CHROME_BIN'):
            path = os.getenv(name)
            if path:
                return path
        # try common system binaries
        for cmd in ('chromium-browser', 'chromium', 'google-chrome', 'google-chrome-stable'):
            path = shutil.which(cmd)
            if path:
                return path
        return None

    launch_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--single-process',
        '--no-zygote'
    ]

    executable_path = find_chrome_executable()
    browser = None
    try:
        if executable_path:
            browser = await launch(headless=True, args=launch_args, executablePath=executable_path, ignoreHTTPSErrors=True)
        else:
            browser = await launch(headless=True, args=launch_args, ignoreHTTPSErrors=True)

        page = await browser.newPage()
        await page.setViewport({'width': 1280, 'height': 800})
        await page.goto('https://aternos.org/login', waitUntil='networkidle2')

        login_email = await page.querySelector('input[type=email], input[name=email], input[name=user], input[name=username], input[placeholder*=Email], input[placeholder*=email]')
        login_password = await page.querySelector('input[type=password]')

        if login_email and login_password:
            await login_email.click({'clickCount': 3})
            await login_email.type(ATERNOS_LOGIN, {'delay': 30})
            await login_password.click({'clickCount': 3})
            await login_password.type(ATERNOS_PASSWORD, {'delay': 30})

            submit_button = await page.querySelector('button[type=submit], input[type=submit]')
            if submit_button:
                await asyncio.gather(page.waitForNavigation(waitUntil='networkidle2'), submit_button.click())
            else:
                await asyncio.gather(page.waitForNavigation(waitUntil='networkidle2'), page.keyboard.press('Enter'))

        await page.goto(ATERNOS_SERVER_URL, waitUntil='networkidle2')
        status_button = await find_button(page, ['start', 'server starten', 'starten', 'anwerfen', 'play'])
        if not status_button:
            raise RuntimeError('Start-Button konnte nicht gefunden werden. Bitte prüfe die Aternos-URL und deine Login-Daten.')

        text = await page.evaluate('(element) => element.innerText || element.value || ""', status_button)
        if any(keyword in text.lower() for keyword in ['stop', 'laufend', 'online', 'running']):
            return 'Der Aternos-Server läuft bereits.', 'already-running'

        await asyncio.gather(page.waitForTimeout(2000), status_button.click())

        result_message = 'Der Start-Vorgang wurde ausgelöst. Der Server sollte gleich hochfahren.'
        for _ in range(10):
            await page.waitForTimeout(4000)
            current_button = await find_button(page, ['stop', 'stopp', 'laufend', 'online', 'running'])
            if current_button:
                current_text = await page.evaluate('(element) => element.innerText || element.value || ""', current_button)
                if any(keyword in current_text.lower() for keyword in ['stop', 'laufend', 'online', 'running']):
                    result_message = 'Der Server ist jetzt gestartet und sollte erreichbar sein.'
                    break
        return result_message, 'started'
    except Exception as e:
        tb = traceback.format_exc()
        msg = str(e)
        hint = (
            "Browser closed unexpectedly. Mögliche Ursachen:\n"
            "- Chromium/Chrome ist nicht installiert oder nicht erreichbar in der Umgebung.\n"
            "- Auf dem Host müssen zusätzliche Start-Flags (z.B. --no-sandbox) erlaubt sein.\n"
            "Lösungsvorschläge:\n"
            "1) Installiere Chromium/Chrome auf dem Host oder weise Katabump an, eine Browser-Binary bereitzustellen.\n"
            "2) Setze die Umgebungsvariable `PUPPETEER_EXECUTABLE_PATH` oder `CHROME_PATH` auf den Pfad zur Chrome/Chromium-Binary.\n"
            "3) Wenn möglich, teste lokal mit `python bot.py` nach `pip install -r requirements.txt`.\n"
        )
        raise RuntimeError(f"Browser launch failed: {msg}\n{hint}\nDebug:\n{tb}")
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass


@tree.command(name='start', description='Startet deinen Aternos Server')
async def start(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        message, status = await start_aternos_server()
        color = 0xffa500 if status == 'already-running' else 0x00ff00
        embed = create_embed('Aternos Server', message, color)
        await interaction.followup.send(embed=embed)
    except Exception as error:
        embed = create_embed('Aternos Server - Fehler', f'Fehler beim Starten des Servers:\n\n{error}', 0xff0000)
        await interaction.followup.send(embed=embed)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=int(GUILD_ID)))
    print(f'Eingeloggt als {client.user}. Slash-Befehl /start ist bereit.')


def main():
    client.run(TOKEN)


if __name__ == '__main__':
    main()
