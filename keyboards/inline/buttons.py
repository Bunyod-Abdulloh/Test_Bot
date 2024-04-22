import random

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, SwitchInlineQueryChosenChat, CallbackGame
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import db


class BattleCallback(CallbackData, prefix="battle"):
    book_name: str
    random: str
    # offer: str


class OfferCallback(CallbackData, prefix="random_opponent"):
    agree_id: int
    book_id: int


class StartPlayingCallback(CallbackData, prefix="start_playing"):
    book_id: int
    battle_id: int


class QuestionsCallback(CallbackData, prefix="questions"):
    question_id: int
    a_correct: str
    b: str
    c: str
    d: str


def check_user_ibuttons(status: str):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🧐 {status}", callback_data="status")
            ]
        ]
    )
    return markup


async def battle_main_ibuttons(back_text: str, back_callback: str):
    all_books = await db.select_all_tables()

    builder = InlineKeyboardBuilder()

    for book in all_books:
        builder.add(
            InlineKeyboardButton(
                text=f"{book['table_name']}", callback_data=f"table_{book['id']}"
            )
        )
    builder.add(
        InlineKeyboardButton(text=f"⬅️ {back_text}", callback_data=f"{back_callback}")
    )
    builder.adjust(1)

    return builder.as_markup()


def battle_ibuttons(random_opponent: str, offer_opponent: str, playing_alone: str, back: str, back_callback: str,
                    book_id: str):

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"😎 {random_opponent}", callback_data=f"book_id:{book_id}")
            ],
            [
                InlineKeyboardButton(text=f"😊 {offer_opponent}", callback_data=f"with_friend:{book_id}")
            ],
            [
                InlineKeyboardButton(text=f"🥷 {playing_alone}", callback_data=f"alone:{book_id}")
            ],
            [
                InlineKeyboardButton(text=f"⬅️ {back}", callback_data=f"{back_callback}")
            ]
        ]
    )
    return markup


def to_offer_ibuttons(agree_text: str, agree_id: int, refusal_text: str, book_id: int):

    callback_factory = OfferCallback(agree_id=agree_id, book_id=book_id)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🎮 {agree_text}", callback_data=callback_factory.pack())
            ],
            [
                InlineKeyboardButton(text=f"❌ {refusal_text}", callback_data=callback_factory.pack())
            ]
        ]
    )
    return markup


def play_battle_ibuttons(start_text: str, book_id: int, battle_id: int):
    callback_factory = StartPlayingCallback(book_id=book_id, battle_id=battle_id)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🚀 {start_text}", callback_data=callback_factory.pack())
            ]
        ]
    )
    return markup


def bot_offer_ibuttons(offer_text: str, full_name: str, bot_link: str):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🤖 {offer_text}", switch_inline_query=f"\n\nFoydalanuvchi {full_name} Sizni bellashuvga "
                                                                f"taklif qilmoqda! Manzil: {bot_link}"
                )
            ]
        ]
    )
    return markup
