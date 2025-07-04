import os
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, START_PIC, AUTO_DELETE_TIME, AUTO_DELETE_MSG, JOIN_REQUEST_ENABLE, FORCE_SUB_CHANNELS
from helper_func import subscribed, decode, get_messages, delete_file
from database.database import add_user, del_user, full_userbase, present_user


@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        string = await decode(base64_string)
        
        # Handle batch links (new format: batch-<id1>-<id2>-<id3>...)
        if string.startswith("batch-"):
            try:
                # Extract message IDs from batch string
                ids_str = string.split("-")[1:]
                base_message_ids = list(map(int, ids_str))
                
                # Convert to actual message IDs
                message_ids = [base_id // abs(client.db_channel.id) for base_id in base_message_ids]
                
                temp_msg = await message.reply("Processing batch...")
                messages = await get_messages(client, message_ids)
                await temp_msg.delete()

                track_msgs = []

                for msg in messages:
                    if bool(CUSTOM_CAPTION) & bool(msg.document):
                        caption = CUSTOM_CAPTION.format(
                            previouscaption="" if not msg.caption else msg.caption.html,
                            filename=msg.document.file_name
                        )
                    else:
                        caption = "" if not msg.caption else msg.caption.html

                    if DISABLE_CHANNEL_BUTTON:
                        reply_markup = msg.reply_markup
                    else:
                        reply_markup = None

                    if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                        try:
                            copied_msg = await msg.copy(
                                chat_id=message.from_user.id,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=reply_markup,
                                protect_content=PROTECT_CONTENT
                            )
                            if copied_msg:
                                track_msgs.append(copied_msg)
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                            copied_msg = await msg.copy(
                                chat_id=message.from_user.id,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=reply_markup,
                                protect_content=PROTECT_CONTENT
                            )
                            if copied_msg:
                                track_msgs.append(copied_msg)
                        except Exception as e:
                            print(f"Error copying message: {e}")
                    else:
                        try:
                            await msg.copy(
                                chat_id=message.from_user.id,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=reply_markup,
                                protect_content=PROTECT_CONTENT
                            )
                            await asyncio.sleep(0.5)
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                            await msg.copy(
                                chat_id=message.from_user.id,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=reply_markup,
                                protect_content=PROTECT_CONTENT
                            )
                        except Exception as e:
                            print(f"Error copying message: {e}")

                if track_msgs and AUTO_DELETE_TIME > 0:
                    delete_data = await client.send_message(
                        chat_id=message.from_user.id,
                        text=AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME)
                    )
                    asyncio.create_task(delete_file(track_msgs, client, delete_data))
                
                return
            except Exception as e:
                await message.reply_text(f"❌ Invalid batch link: {str(e)}")
                return
        
        # Handle old format links (single and range)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end+1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        else:
            return

        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        track_msgs = []

        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            if AUTO_DELETE_TIME and AUTO_DELETE_TIME > 0:
                try:
                    copied_msg = await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    if copied_msg:
                        track_msgs.append(copied_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    copied_msg = await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    if copied_msg:
                        track_msgs.append(copied_msg)
                except Exception as e:
                    print(f"Error copying message: {e}")
            else:
                try:
                    await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                except Exception as e:
                    print(f"Error copying message: {e}")

        if track_msgs and AUTO_DELETE_TIME > 0:
            delete_data = await client.send_message(
                chat_id=message.from_user.id,
                text=AUTO_DELETE_MSG.format(time=AUTO_DELETE_TIME)
            )
            asyncio.create_task(delete_file(track_msgs, client, delete_data))
        
        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data="about"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ]
        )
        if START_PIC:
            await message.reply_photo(
                photo=START_PIC,
                caption=START_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=message.from_user.id
                ),
                reply_markup=reply_markup,
                quote=True
            )
        else:
            await message.reply_text(
                text=START_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=message.from_user.id
                ),
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                quote=True
            )
        return

    
#=====================================================================================##

WAIT_MSG = "<b>Processing ...</b>"

REPLY_ERROR = "<code>Use this command as a replay to any telegram message with out any spaces.</code>"

#=====================================================================================##


@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    # Only show buttons if force sub channels are configured
    if not FORCE_SUB_CHANNELS:
        return await start_command(client, message)
    
    # Create buttons for all force sub channels
    buttons = []
    
    # Get force sub channels from bot instance
    force_subs = getattr(client, 'force_subs', {})
    
    if not force_subs:
        return await message.reply("❌ Force sub channels not configured properly")
    
    # Create buttons in groups of 2
    row_buttons = []
    for i, (channel_id, channel_info) in enumerate(force_subs.items()):
        # Create button with generic text
        row_buttons.append(
            InlineKeyboardButton(
                "Join Channel",  # Changed to generic text
                url=channel_info['link']
            )
        )
        
        # Create new row after every 2 buttons
        if len(row_buttons) == 2 or i == len(force_subs) - 1:
            buttons.append(row_buttons)
            row_buttons = []
    
    # Add Try Again button
    try:
        start_param = message.command[1]
        try_again_link = f"https://t.me/{client.username}?start={start_param}"
    except IndexError:
        try_again_link = f"https://t.me/{client.username}"
    
    buttons.append([InlineKeyboardButton("🔄 Try Again", url=try_again_link)])

    # Format the generic message
    await message.reply(
        text=(
            f"Hello {message.from_user.mention}!\n\n"
            "📢 **You need to join our channels to use this bot.**\n\n"
            "Please join all channels using the buttons below and then try again."
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
