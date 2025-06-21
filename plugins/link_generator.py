from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id

# Store user batch sessions {user_id: [message_ids]}
user_batch_sessions = {}

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    user_id = message.from_user.id
    user_batch_sessions[user_id] = []
    
    # Initialize batch session
    await start_batch_session(client, message)

async def start_batch_session(client, message):
    user_id = message.from_user.id
    stored_count = len(user_batch_sessions.get(user_id, []))
    
    text = f"📦 Batch Session\n\nStored Messages: {stored_count}\n\nPlease click your preferred button"
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add More", callback_data="add_more"),
            InlineKeyboardButton("🔗 Generate Link", callback_data="generate_link")
        ],
        [
            InlineKeyboardButton("❌ Cancel Batch", callback_data="cancel_batch")
        ]
    ])
    
    if "batch_session_msg" not in user_batch_sessions[user_id]:
        msg = await message.reply_text(text, reply_markup=keyboard)
        user_batch_sessions[user_id].append("batch_session_msg")
        user_batch_sessions[user_id].append(msg.id)
    else:
        msg_id = user_batch_sessions[user_id][1]
        await client.edit_message_text(
            chat_id=user_id,
            message_id=msg_id,
            text=text,
            reply_markup=keyboard
        )

@Bot.on_callback_query(filters.regex(r'^add_more$'))
async def add_more_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_batch_sessions or not user_batch_sessions[user_id]:
        await callback_query.answer("Session expired! Start a new batch with /batch")
        return
    
    await callback_query.answer("Please send next message...")
    
    # Ask user to send next message
    msg = await client.send_message(
        chat_id=user_id,
        text="Please forward the next message from DB Channel (with Quotes) or send the DB Channel Post Link"
    )
    
    # Store the message ID to track the session
    user_batch_sessions[user_id].append(msg.id)

@Bot.on_message(filters.private & filters.user(ADMINS) & 
                ~filters.command(['start','users','broadcast','batch','genlink','stats']))
async def handle_batch_message(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_batch_sessions or not user_batch_sessions[user_id]:
        return
    
    # Check if this is a response to our "add more" prompt
    if message.reply_to_message and message.reply_to_message.id in user_batch_sessions[user_id]:
        base_message_id = await get_message_id(client, message)
        if base_message_id:
            # Multiply by abs(channel_id) to obfuscate
            obfuscated_id = base_message_id * abs(client.db_channel.id)
            if "message_ids" not in user_batch_sessions[user_id]:
                user_batch_sessions[user_id].append("message_ids")
                user_batch_sessions[user_id].append([])
            
            # Add to message IDs
            message_ids = user_batch_sessions[user_id][-1]
            message_ids.append(obfuscated_id)
            
            # Remove the prompt message ID
            user_batch_sessions[user_id].remove(message.reply_to_message.id)
            
            # Update batch session
            await start_batch_session(client, message)
        else:
            await message.reply("❌ Error\n\nNot a valid message from DB Channel. Please try again.")
            await start_batch_session(client, message)

@Bot.on_callback_query(filters.regex(r'^generate_link$'))
async def generate_link_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_batch_sessions or not user_batch_sessions[user_id]:
        await callback_query.answer("Session expired! Start a new batch with /batch")
        return
    
    # Get stored message IDs
    if "message_ids" not in user_batch_sessions[user_id] or not user_batch_sessions[user_id][-1]:
        await callback_query.answer("No messages added yet!", show_alert=True)
        return
    
    message_ids = user_batch_sessions[user_id][-1]
    
    # Create batch string
    if len(message_ids) == 1:
        # Single message
        string = f"get-{message_ids[0]}"
    else:
        # Multiple messages
        string = f"batch-{'-'.join(str(msg_id) for msg_id in message_ids)}"
    
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    # Create shareable button
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')],
        [InlineKeyboardButton("✏️ Start New Batch", callback_data="new_batch")]
    ])
    
    # Send final link
    await callback_query.message.edit_text(
        f"<b>✅ Batch Link Created</b>\n\n{link}\n\n"
        f"Total Messages: {len(message_ids)}",
        reply_markup=reply_markup
    )
    
    # Clear session
    del user_batch_sessions[user_id]

@Bot.on_callback_query(filters.regex(r'^cancel_batch$|^new_batch$'))
async def cancel_batch_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in user_batch_sessions:
        del user_batch_sessions[user_id]
    
    if callback_query.data == "new_batch":
        await callback_query.answer("Starting new batch...")
        await batch.__call__(client, callback_query.message)
    else:
        await callback_query.message.edit_text("❌ Batch session cancelled")
        await callback_query.answer()
