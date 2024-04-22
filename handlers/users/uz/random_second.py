from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from handlers.users.uz.random_first import send_result_or_continue, generate_question
from keyboards.inline.buttons import OfferCallback, play_battle_ibuttons
from loader import db, bot

router = Router()


@router.callback_query(OfferCallback.filter())
async def get_opponent(call: types.CallbackQuery, callback_data: OfferCallback, state: FSMContext):
    first_player_id = callback_data.agree_id
    second_player_id = call.from_user.id
    book_id = callback_data.book_id
    fullname = call.from_user.full_name

    book_name = await db.select_book_by_id(
        id_=book_id
    )
    # Temporary jadvaliga user ma'lumotlarini qo'shib battle idsini olish
    id_ = await db.add_answer(
        telegram_id=first_player_id
    )
    battle_id = id_[0]

    await bot.send_message(
        chat_id=first_player_id,
        text=f"Foydalanuvchi {fullname} {book_name['table_name']} kitobi bo'yicha bellashuvga rozilik bildirdi!",
        reply_markup=play_battle_ibuttons(
            start_text="Boshlash", book_id=book_id, battle_id=battle_id
        )
    )
    c_two = 1
    await state.update_data(
        c_two=c_two
    )
    # Users jadvalida userga game_on yoqish
    await db.edit_status_users(
        game_on=True, telegram_id=second_player_id
    )
    await generate_question(
        book_id=book_id, counter=c_two, call=call, battle_id=battle_id, opponent=True
    )
    # Results jadvaliga userni qo'shish
    await db.add_gamer(
        telegram_id=second_player_id, book_id=book_id
    )


@router.callback_query(F.data.startswith("s_question:a"))
async def get_question_answer_a(call: types.CallbackQuery, state: FSMContext):
    data = await state.update_data()
    c = data['c_two']
    telegram_id = call.from_user.id
    book_id = int(call.data.split(":")[2])
    book_name = await db.select_book_by_id(id_=book_id)
    battle_id = int(call.data.split(":")[3])
    await send_result_or_continue(
        first_telegram_id=telegram_id, battle_id=battle_id, counter=c, answer_emoji="✅", correct_emoji="✅",
        wrong_emoji="❌", book_id=book_id, book_name=book_name['table_name'], call=call, state=state, opponent=True,
        counter_key="c_two"
    )


second_answer_filter = (F.data.startswith("s_question:b") | F.data.startswith("s_question:c") |
                        F.data.startswith("s_question:d"))


@router.callback_query(second_answer_filter)
async def get_question_answer(call: types.CallbackQuery, state: FSMContext):
    data = await state.update_data()
    c = data['c_two']
    telegram_id = call.from_user.id
    book_id = int(call.data.split(":")[2])
    book_name = await db.select_book_by_id(id_=book_id)
    battle_id = int(call.data.split(":")[3])
    await send_result_or_continue(
        first_telegram_id=telegram_id, battle_id=battle_id, counter=c, answer_emoji="❌", correct_emoji="✅",
        wrong_emoji="❌", book_id=book_id, book_name=book_name['table_name'], call=call, state=state, opponent=True,
        counter_key="c_two"
    )
