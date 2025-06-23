from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import time
import asyncio
import logging

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

        # DB Channel access with 2-minute waiting period
        start_time = time.time()
        timeout = 120  # 2 minutes
        channel_ready = False
        
        self.LOGGER(__name__).info(f"⏳ Waiting for admin access to DB channel ID: {CHANNEL_ID}")
        self.LOGGER(__name__).info("Please make the bot admin in the DB channel within 2 minutes...")
        
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
                self.LOGGER(__name__).warning(f"⏳ Waiting for DB channel admin privileges... ({int(timeout - (time.time() - start_time))}s left)")
                await asyncio.sleep(10)  # Check every 10 seconds
        
        if not channel_ready:
            self.LOGGER(__name__).error(f"❌ Failed to access DB channel {CHANNEL_ID} after 2 minutes")
            self.LOGGER(__name__).error("Please ensure:")
            self.LOGGER(__name__).error("1. Bot is admin in the channel")
            self.LOGGER(__name__).error("2. CHANNEL_ID is correct")
            self.LOGGER(__name__).error("3. Channel exists and bot is added")
            self.LOGGER(__name__).info("\nBot stopped. Join https://t.me/CodeXBotzSupport for support")
            sys.exit(1)

        # Force Sub Channel access with 2-minute waiting period
        if FORCE_SUB_CHANNEL and FORCE_SUB_CHANNEL != 0:
            start_time = time.time()
            timeout = 120  # 2 minutes
            force_sub_ready = False
            
            self.LOGGER(__name__).info(f"⏳ Waiting for admin access to force sub channel ID: {FORCE_SUB_CHANNEL}")
            self.LOGGER(__name__).info("Please make the bot admin in the force sub channel within 2 minutes...")
            
            while time.time() - start_time < timeout:
                try:
                    force_chat = await self.get_chat(FORCE_SUB_CHANNEL)
                    
                    # Try to get or create invite link
                    try:
                        link = force_chat.invite_link
                        if not link:
                            link = await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                    except:
                        link = None
                    
                    if link:
                        self.invitelink = link
                        force_sub_ready = True
                        self.LOGGER(__name__).info(f"✅ Successfully accessed Force Sub Channel: {force_chat.title}!")
                        break
                except Exception as e:
                    self.LOGGER(__name__).warning(f"⏳ Waiting for force sub channel admin privileges... ({int(timeout - (time.time() - start_time))}s left)")
                    await asyncio.sleep(10)  # Check every 10 seconds
            
            if not force_sub_ready:
                self.LOGGER(__name__).error(f"❌ Failed to access force sub channel {FORCE_SUB_CHANNEL} after 2 minutes")
                self.LOGGER(__name__).error("Please ensure:")
                self.LOGGER(__name__).error("1. Bot is admin in the force sub channel")
                self.LOGGER(__name__).error("2. FORCE_SUB_CHANNEL is correct")
                self.LOGGER(__name__).error("3. Channel exists and bot is added")
                self.LOGGER(__name__).info("\nBot stopped. Join https://t.me/CodeXBotzSupport for support")
                sys.exit(1)

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"🤖 Bot Running! DB Channel: {self.db_channel.title} (ID: {self.db_channel.id})")
        
        if FORCE_SUB_CHANNEL:
            self.LOGGER(__name__).info(f"🔒 Force Sub Enabled: {self.invitelink}")
        
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
