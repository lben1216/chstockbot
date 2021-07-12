from asyncio import sleep

from typing import Callable, Dict, List, Union
from pyrogram.types import CallbackQuery,User
from pyrogram.types.bots_and_keyboards.inline_keyboard_button import InlineKeyboardButton
from pyrogram.types.bots_and_keyboards.inline_keyboard_markup import InlineKeyboardMarkup

from ..services.callsmusic import callsmusic
from ..services.queues import queues

from pyrogram import Client,filters
from ..config import BOT_USERNAME,BOT_ID

instances: Dict[int, List] = {}
bot:Client = None

async def init_instance(chat_id):
    if chat_id not in instances:
        instances[chat_id] = None
        return
    if instances[chat_id]:
        await instances[chat_id][0].delete()
        instances[chat_id] = None

def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client:Client, cb:CallbackQuery):
        chat_id = cb.message.chat.id
        mm,song = instances[chat_id]
        admins = []
        async for i in client.iter_chat_members(chat_id, filter="administrators"):
            admins.append(i.user.id)
        admins.append(song['user'].id)
        if cb.from_user.id in admins:
            return await func(client, cb)
        else:
            await cb.answer("只能点歌者和管理员才能跳过这个音乐哦~", show_alert=True)
            return
    return decorator


@Client.on_callback_query(filters.regex("m_skip"))
@cb_admin_check
async def callback_query_skip(client:Client, cb: CallbackQuery):
    chat_id = cb.message.chat.id
    mm,song = instances[chat_id]
    await mm.delete()
    await callsmusic.skip(chat_id)
    m = await client.send_message(chat_id, "跳过歌曲!")
    await sleep(5)
    await m.delete()
    return

def listy(queue:Dict):
    liste=""
    i = 1
    if len(queue) > 0:
        for song in queue:
            if i == 11:
                break
            liste += f"{i}. `{song['title']}` - 点播者 {song['user'].first_name}\n"
            i += 1
        liste += f"\n 共有{len(queue)}首歌等待播放"
        return liste
    else:
        return None


@Client.on_callback_query(filters.regex("m_queue"))
async def message_queue(client:Client, cb: CallbackQuery):
    chat_id = cb.message.chat.id
    q = queues.getlist(chat_id)
    liste = listy(q)
    if liste:
        m = await client.send_message(chat_id, f"{liste}\n查询者:{cb.from_user.mention}",disable_notification=True)
        await sleep(10)
        await m.delete()
        return
    else:
        await client.answer_callback_query(cb.id, "暂时没有歌曲等待播放哦~", show_alert=True)
        return

async def send_playing(chat_id: Union[int,str],song:Dict):
    await init_instance(chat_id)
    mm = await bot.send_photo(
        chat_id,
        song['thumbnail'],
        caption=f"正在播放 {song['user'].first_name} 点播的\n`{song['title']}`\n来自于 `{song['singers']}`\n时长 {song['sduration']}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("跳过",callback_data="m_skip"),
            InlineKeyboardButton("等待队列",callback_data="m_queue")
        ]]),disable_notification=True)
    instances[chat_id] = [mm,song]

async def clean(chat_id):
    await init_instance(chat_id)