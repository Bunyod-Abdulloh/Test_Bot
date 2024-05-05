import random
from datetime import datetime

from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.users.battle_main import result_time_game
from handlers.users.random_first import first_text
from loader import db

router = Router()


async def generate_question_alone(book_id, counter, call: types.CallbackQuery):
    questions = await db.select_all_questions(table_name=f"table_{book_id}")

    letters = ["A", "B", "C", "D"]

    a = ["a", f"{questions[0][2]}"]
    b = ["b", f"{questions[0][3]}"]
    c = ["c", f"{questions[0][4]}"]
    d = ["d", f"{questions[0][5]}"]

    answers = [a, b, c, d]

    random.shuffle(answers)

    answers_dict = dict(zip(letters, answers))

    questions_text = str()

    for letter, question in answers_dict.items():
        questions_text += f"{letter}) {question[1]}\n"

    builder = InlineKeyboardBuilder()
    for letter, callback in answers_dict.items():
        builder.add(
            types.InlineKeyboardButton(
                text=f"{letter}", callback_data=f"al_question:{callback[0]}:{book_id}"
            )
        )
    builder.adjust(2, 2)

    await call.message.edit_text(
        text=f"{counter}. {questions[0]['question']}\n\n"
             f"{questions_text}",
        reply_markup=builder.as_markup()
    )


async def send_alone_result_or_continue(call: types.CallbackQuery, answer_emoji):
    telegram_id = call.from_user.id
    book_id = int(call.data.split(":")[2])
    book_name = await db.select_book_by_id(id_=book_id)
    counter_db = await db.select_user_counter(
        telegram_id=telegram_id, battle_id=0
    )
    counter = counter_db['counter']
    if counter >= 10:
        await db.add_answer_to_temporary(
            telegram_id=telegram_id, battle_id=0, question_number=counter, answer=answer_emoji, game_status="ON"
        )
        await db.update_all_game_status(
            game_status="OVER", telegram_id=telegram_id, battle_id=0
        )
        # User o'yinni tugatgan vaqtni DBga yozish
        end_time = datetime.now()
        await db.end_answer_to_temporary(
            telegram_id=telegram_id, battle_id=0, game_status="OFF", end_time=end_time
        )
        start_time = await db.select_start_time(
            telegram_id=telegram_id, battle_id=0
        )
        # O'yin boshlangan va tugagan vaqtni hisoblash
        difference = await result_time_game(
            start_time=start_time[0][0], end_time=end_time
        )
        # To'g'ri javoblar soni
        correct_answers = await db.count_answers(
            telegram_id=telegram_id, answer="✅"
        )
        # Noto'g'ri javoblar soni
        wrong_answers = await db.count_answers(
            telegram_id=telegram_id, answer="❌"
        )
        # To'g'ri javoblar sonini Results jadvalidan yangilash
        await db.update_results(
            results=correct_answers, telegram_id=telegram_id, book_id=book_id, time_result=difference
        )
        # Results jadvalidan user reytingini kitob bo'yicha aniqlash
        rating_book = await db.get_rating_by_result(
            book_id=book_id
        )

        rating_book_ = int()
        book_points = int()

        for index, result in enumerate(rating_book):
            if result['telegram_id'] == telegram_id:
                rating_book_ += index + 1
                book_points += result['result']
                break

        # Results jadvalidan userning umumiy reytingini aniqlash
        all_rating = await db.get_rating_all()
        all_rating_ = int()
        all_points = int()
        for index, result in enumerate(all_rating):
            if result['telegram_id'] == telegram_id:
                all_rating_ += index + 1
                all_points += result['result']
                break
        f_text = first_text(
            book_name=book_name['table_name'], result_text="Sizning natijangiz", correct_answers=correct_answers,
            wrong_answers=wrong_answers, time=difference, book_points=book_points, book_rating=rating_book_,
            all_points=all_points, all_rating=all_rating_
        )
        await call.message.edit_text(
            text=f_text
        )
        await db.edit_status_users(
            game_on=False, telegram_id=telegram_id
        )
        # Natijani Temporary jadvalidan tozalash
        await db.delete_from_temporary(
            telegram_id=telegram_id
        )
        # Counter jadvalidan user ma'lumotlarini tozalash
        await db.delete_from_counter(
            telegram_id=telegram_id
        )
    else:
        await db.add_answer_to_temporary(
            telegram_id=telegram_id, battle_id=0, question_number=counter, answer=answer_emoji, game_status="ON"
        )
        counter = counter_db['counter'] + 1
        await generate_question_alone(
            book_id=book_id, call=call, counter=counter
        )
        await db.update_counter(
            counter=1, battle_id=0, telegram_id=telegram_id
        )


@router.callback_query(F.data.startswith("alone:"))
async def alone_first(call: types.CallbackQuery):
    book_id = int(call.data.split(":")[1])
    telegram_id = call.from_user.id
    c = 1
    await generate_question_alone(
        book_id=book_id, call=call, counter=c
    )
    # Counter jadvaliga savol tartib raqamini kiritish
    await db.add_to_counter(
        telegram_id=telegram_id, battle_id=0, counter=c
    )
    # Userni Results jadvalida bor yo'qligini tekshirish
    check_in_results = await db.select_user_in_results(
        telegram_id=telegram_id, book_id=book_id
    )
    if not check_in_results:
        # Results jadvaliga userni qo'shish
        await db.add_gamer(
            telegram_id=telegram_id, book_id=book_id
        )
    # Users jadvalida userga game_on yoqish
    await db.edit_status_users(
        game_on=True, telegram_id=telegram_id
    )

    start_time = datetime.now()
    await db.start_time_to_temporary(
        telegram_id=telegram_id, battle_id=0, game_status="ON", start_time=start_time
    )


@router.callback_query(F.data.startswith("al_question:a"))
async def alone_second(call: types.CallbackQuery):
    await send_alone_result_or_continue(
        call=call, answer_emoji="✅"
    )


magic_alone = (F.data.startswith("al_question:b") | F.data.startswith("al_question:c") |
               F.data.startswith("al_question:d"))


@router.callback_query(magic_alone)
async def alone_third(call: types.CallbackQuery):
    await send_alone_result_or_continue(
        call=call, answer_emoji="❌"
    )