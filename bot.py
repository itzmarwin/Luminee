from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import time  # Added import
import asyncio  # Added import

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT


ascii_art = """
░█████╗░░█████╗░██████╗░███████╗██╗░░██╗██████╗░░█████╗░████████╗███████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗╚══██╔══╝╚════██║
██║░░╚═╝██║░░██║██║░░██║█████╗░░░╚███╔╝░██████╦╝██║░░██║░░░██║░░░░░███╔═╝
██║░░██╗██║░░██║██║░░██║██╔══╝░░░██╔██╗░██╔══██╗██║░░██║░░░██║░░░██╔══╝░░
╚█████╔╝╚█████╔╝██████╔╝███████╗██╔╝╚██╗██████╦╝╚█████╔╝░░░██║░░░███████╗
░╚════╝░░╚════╝░╚═════╝░╚══════╝╚═╝░░╚═╝╚═════╝░░╚════╝░░░░╚═╝░░░╚══════╝
"""

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Force sub channel handling
        if FORCE_SUB_CHANNEL:
            try:
                link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                    link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                self.LOGGER(__name__).warning(f"Please Double check the FORCE_SUB_CHANNEL value and Make sure Bot is Admin in channel with Invite Users via Link Permission, Current Force Sub Channel Value: {FORCE_SUB_CHANNEL}")
                self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/CodeXBotzSupport for support")
                sys.exit()

        # DB Channel access with 2-minute waiting period
        start_time = time.time()
        timeout = 120  # 2 minutes
        channel_ready = False
        
        self.LOGGER(__name__).info(f"⏳ Waiting for admin access to channel ID: {CHANNEL_ID}")
        self.LOGGER(__name__).info("Please make the bot admin in the channel within 2 minutes...")
        
        while time.time() - start_time < timeout:
            try:
                db_channel = await self.get_chat(CHANNEL_ID)
                self.db_channel = db_channel
                test = await self.send_message(chat_id=db_channel.id, text="🔧 Bot connection test")
                await test.delete()
                channel_ready = True
                self.LOGGER(__name__).info("✅ Successfully accessed DB Channel!")
                break
            except Exception as e:
                self.LOGGER(__name__).warning(f"⏳ Waiting for admin privileges... ({int(timeout - (time.time() - start_time))}s left)")
                await asyncio.sleep(10)  # Check every 10 seconds
        
        if not channel_ready:
            self.LOGGER(__name__).error(f"❌ Failed to access channel {CHANNEL_ID} after 2 minutes")
            self.LOGGER(__name__).error("Please ensure:")
            self.LOGGER(__name__).error("1. Bot is admin in the channel")
            self.LOGGER(__name__).error("2. CHANNEL_ID is correct")
            self.LOGGER(__name__).error("3. Channel exists and bot is added")
            self.LOGGER(__name__).info("\nBot stopped. Join https://t.me/CodeXBotzSupport for support")
            sys.exit(1)

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"🤖 Bot Running! DB Channel: {self.db_channel.title} (ID: {self.db_channel.id})")
        print(ascii_art)
        print("""🚀 Welcome to File Sharing Bot""")
        self.username = usr_bot_me.username
        
        # Web server setup
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("🛑 Bot stopped.")
