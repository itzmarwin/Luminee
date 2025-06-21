from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id
import asyncio

# Store user batch sessions {user_id: [message_ids]}
user_batch_sessions = {}

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    user_id = message.from_user.id
    user_batch_sessions[user_id] = {
        'message_ids': [],
        'session_active': True
    }
    await start_batch_session(client, message)

async def start_batch_session(client, message):
    user_id = message.from_user.id
    session = user_batch_sessions.get(user_id)
    
    if not session or not session['session_active']:
        await message.reply("Session expired! Start a new batch with /batch")
        return
        
    stored_count = len(session['message_ids'])
    text = f"📦 Batch Session\n\nStored Messages: {stored_count}\n\nPlease click your preferred button"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add More", callback_data="add_more")],
        [InlineKeyboardButton("🔗 Generate Link", callback_data="generate_link")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")]
    ])
    
    if 'session_msg_id' not in session:
        msg = await message.reply_text(text, reply_markup=keyboard)
        session['session_msg_id'] = msg.id
    else:
        try:
            await client.edit_message_text(
                chat_id=user_id,
                message_id=session['session_msg_id'],
                text=text,
                reply_markup=keyboard
            )
        except:
            # Message might be deleted, create new one
            msg = await message.reply_text(text, reply_markup=keyboard)
            session['session_msg_id'] = msg.id

@Bot.on_callback_query(filters.regex(r'^add_more$'))
async def add_more_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = user_batch_sessions.get(user_id)
    
    if not session or not session['session_active']:
        await callback_query.answer("Session expired! Start a new batch with /batch")
        return
        
    await callback_query.answer()
    
    # Ask user to send next message
    prompt = await client.send_message(
        chat_id=user_id,
        text="Please forward a message from your DB channel or send a DB Channel Post Link"
    )
    
    # Store the prompt message ID
    session['prompt_msg_id'] = prompt.id

@Bot.on_message(filters.private & filters.user(ADMINS) & 
                ~filters.command(['start','users','broadcast','batch','genlink','stats']))
async def handle_batch_message(client: Client, message: Message):
    user_id = message.from_user.id
    session = user_batch_sessions.get(user_id)
    
    if not session or not session['session_active']:
        return
        
    # Check if this is a response to our "add more" prompt
    if 'prompt_msg_id' in session and message.reply_to_message_id == session['prompt_msg_id']:
        msg_id = await get_message_id(client, message)
        if msg_id:
            # Store the obfuscated message ID
            obfuscated_id = msg_id * abs(client.db_channel.id)
            session['message_ids'].append(obfuscated_id)
            
            # Delete the prompt message
            try:
                await client.delete_messages(user_id, session['prompt_msg_id'])
            except:
                pass
            del session['prompt_msg_id']
            
            # Update batch session
            await start_batch_session(client, message)
        else:
            await message.reply("❌ Error: Not a valid message from DB Channel")
            await start_batch_session(client, message)

@Bot.on_callback_query(filters.regex(r'^generate_link$'))
async def generate_link_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    session = user_batch_sessions.get(user_id)
    
    if not session or not session['session_active']:
        await callback_query.answer("Session expired! Start a new batch with /batch")
        return
        
    message_ids = session['message_ids']
    
    if not message_ids:
        await callback_query.answer("No messages added yet!", show_alert=True)
        return
    
    # Create batch string
    if len(message_ids) == 1:
        string = f"get-{message_ids[0]}"
    else:
        string = f"batch-{'-'.join(str(msg_id) for msg_id in message_ids)}"
    
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    
    # Create shareable button
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')],
        [InlineKeyboardButton("🔄 Start New Batch", callback_data="new_batch")]
    ])
    
    # Send final link
    await callback_query.message.edit_text(
        f"<b>✅ Batch Link Created</b>\n\n{link}\n\n"
        f"Total Messages: {len(message_ids)}",
        reply_markup=reply_markup
    )
    
    # Clear session
    session['session_active'] = False

@Bot.on_callback_query(filters.regex(r'^cancel_batch$'))
async def cancel_batch_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_batch_sessions:
        session = user_batch_sessions[user_id]
        session['session_active'] = False
        
        try:
            await client.delete_messages(user_id, session['session_msg_id'])
        except:
            pass
        
    await callback_query.message.edit_text("❌ Batch session cancelled")

@Bot.on_callback_query(filters.regex(r'^new_batch$'))
async def new_batch_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.answer("Starting new batch...")
    await batch.__call__(client, callback_query.message)
