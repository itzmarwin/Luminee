from aiohttp import web
from plugins import web_server
from config import FORCE_SUB_CHANNELS, JOIN_REQUEST_ENABLE  # Added JOIN_REQUEST_ENABLE

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import time
import asyncio
import logging

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNELS, CHANNEL_ID, PORT, JOIN_REQUEST_ENABLE  # Added JOIN_REQUEST_ENABLE

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
        self.force_subs = {}  # Store force sub channel info

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

        # Force Sub Channels with 2-minute waiting period for each
        if FORCE_SUB_CHANNELS:
            for channel_id in FORCE_SUB_CHANNELS:
                start_time = time.time()
                timeout = 120  # 2 minutes
                channel_ready = False
                
                self.LOGGER(__name__).info(f"⏳ Waiting for admin access to force sub channel ID: {channel_id}")
                self.LOGGER(__name__).info("Please make the bot admin in this channel within 2 minutes...")
                
                while time.time() - start_time < timeout:
                    try:
                        chat = await self.get_chat(channel_id)
                        
                        # Generate appropriate invite link based on join request setting
                        if JOIN_REQUEST_ENABLE:
                            try:
                                # Create join request link
                                invite = await self.create_chat_invite_link(
                                    chat_id=channel_id,
                                    creates_join_request=True
                                )
                                link = invite.invite_link
                                self.LOGGER(__name__).info(f"Created join request link for {channel_id}")
                            except Exception as e:
                                self.LOGGER(__name__).error(f"Failed to create join request link: {e}")
                                link = None
                        else:
                            try:
                                # Get or create regular invite link
                                link = chat.invite_link
                                if not link:
                                    link = await self.export_chat_invite_link(channel_id)
                            except Exception as e:
                                self.LOGGER(__name__).error(f"Failed to get invite link: {e}")
                                link = None
                        
                        if link:
                            self.force_subs[channel_id] = {
                                "title": chat.title,
                                "link": link
                            }
                            channel_ready = True
                            self.LOGGER(__name__).info(f"✅ Successfully accessed Force Sub Channel: {chat.title}!")
                            break
                    except Exception as e:
                        remaining = int(timeout - (time.time() - start_time))
                        self.LOGGER(__name__).warning(f"⏳ Waiting for admin privileges... ({remaining}s left)")
                        await asyncio.sleep(10)
                
                if not channel_ready:
                    self.LOGGER(__name__).error(f"❌ Failed to access channel {channel_id} after 2 minutes")
                    self.LOGGER(__name__).error("Please ensure:")
                    self.LOGGER(__name__).error("1. Bot is admin in the channel")
                    self.LOGGER(__name__).error("2. Channel ID is correct")
                    self.LOGGER(__name__).error("3. Channel exists and bot is added")
                    sys.exit(1)

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"🤖 Bot Running! DB Channel: {self.db_channel.title} (ID: {self.db_channel.id})")
        
        if FORCE_SUB_CHANNELS:
            channel_list = "\n".join(
                [f"• {info['title']} ({channel_id})" 
                 for channel_id, info in self.force_subs.items()]
            )
            self.LOGGER(__name__).info(f"🔒 Force Sub Enabled for {len(FORCE_SUB_CHANNELS)} channels:\n{channel_list}")
        
        # Log join request status
        if JOIN_REQUEST_ENABLE:
            self.LOGGER(__name__).info("🛡️ Join Request System: ENABLED")
        else:
            self.LOGGER(__name__).info("🔓 Join Request System: DISABLED")
        
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
