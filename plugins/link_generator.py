from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id
import asyncio

# Store user batch sessions {user_id: [message_ids]}
user_batch_sessions = {}

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch_command(client: Client, message: Message):
    user_id = message.from_user.id
    # Start new session
    user_batch_sessions[user_id] = {
        'messages': [],
        'waiting_for_message': True,
        'session_msg_id': None
    }
    
    # Ask for first message
    prompt = await message.reply(
        "📦 <b>Batch Session Started</b>\n\n"
        "Please forward the first message from your DB channel or send the DB Channel Post Link",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")]])
    )
    
    # Store the prompt message ID
    user_batch_sessions[user_id]['session_msg_id'] = prompt.id

@Bot.on_message(filters.private & filters.user(ADMINS) & 
                ~filters.command(['start','users','broadcast','batch','genlink','stats']))
async def handle_batch_message(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_batch_sessions:
        return
        
    session = user_batch_sessions[user_id]
    
    if not session.get('waiting_for_message'):
        return
    
    # Get message ID from forwarded message or link
    msg_id = await get_message_id(client, message)
    if not msg_id:
        await message.reply("❌ Error: Not a valid message from DB Channel. Please try again.")
        return
    
    # Store obfuscated message ID
    obfuscated_id = msg_id * abs(client.db_channel.id)
    session['messages'].append(obfuscated_id)
    session['waiting_for_message'] = False
    
    # Show batch menu
    await show_batch_menu(client, user_id, "✅ Message added to batch!")

async def show_batch_menu(client: Client, user_id: int, status: str = ""):
    if user_id not in user_batch_sessions:
        return
        
    session = user_batch_sessions[user_id]
    count = len(session['messages'])
    
    text = (
        f"📦 <b>Batch Session</b>\n\n"
        f"{status}\n"
        f"Stored Messages: {count}\n\n"
        "Please click your preferred button:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add More Messages", callback_data="add_more")],
        [InlineKeyboardButton("🔗 Generate Batch Link", callback_data="generate_batch")],
        [InlineKeyboardButton("❌ End Session", callback_data="cancel_batch")]
    ])
    
    try:
        if session['session_msg_id']:
            await client.edit_message_text(
                chat_id=user_id,
                message_id=session['session_msg_id'],
                text=text,
                reply_markup=keyboard
            )
    except:
        # If message doesn't exist, create a new one
        msg = await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard
        )
        session['session_msg_id'] = msg.id

@Bot.on_callback_query(filters.regex(r'^add_more$'))
async def add_more_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_batch_sessions:
        await callback_query.answer("Session expired! Start a new batch with /batch")
        return
        
    session = user_batch_sessions[user_id]
    session['waiting_for_message'] = True
    
    await callback_query.answer("Please send next message...")
    
    # Update menu message to show we're waiting for input
    try:
        await client.edit_message_text(
            chat_id=user_id,
            message_id=session['session_msg_id'],
            text=(
                "📦 <b>Batch Session</b>\n\n"
                "Waiting for your next message...\n"
                f"Stored Messages: {len(session['messages']}\n\n"
                "Please forward a message from your DB channel or send a DB Channel Post Link"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")]])
        )
    except:
        pass

@Bot.on_callback_query(filters.regex(r'^generate_batch$'))
async def generate_batch_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_batch_sessions:
        await callback_query.answer("Session expired! Start a new batch with /batch")
        return
        
    session = user_batch_sessions[user_id]
    messages = session['messages']
    
    if not messages:
        await callback_query.answer("No messages added yet!", show_alert=True)
        return
    
    # Create batch string
    if len(messages) == 1:
        string = f"get-{messages[0]}"
    else:
        string = f"batch-{'-'.join(str(msg_id) for msg_id in messages)}"
    
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    # Create shareable button
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')],
        [InlineKeyboardButton("🔄 Start New Batch", callback_data="new_batch")]
    ])
    
    # Send final link
    await callback_query.message.edit_text(
        f"<b>✅ Batch Link Created</b>\n\n"
        f"{link}\n\n"
        f"Total Messages: {len(messages)}",
        reply_markup=reply_markup
    )
    
    # Clear session
    del user_batch_sessions[user_id]

@Bot.on_callback_query(filters.regex(r'^cancel_batch$'))
async def cancel_batch_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_batch_sessions:
        del user_batch_sessions[user_id]
    
    await callback_query.message.edit_text("❌ Batch session cancelled")

@Bot.on_callback_query(filters.regex(r'^new_batch$'))
async def new_batch_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.answer("Starting new batch...")
    await batch_command(client, callback_query.message)
