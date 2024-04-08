import asyncio
import random

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.users.uz.start import uz_start_buttons
from keyboards.inline.buttons import battle_ibuttons, battle_main_ibuttons, BattleCallback, to_offer_ibuttons, \
    OfferCallback, play_battle_ibuttons, StartPlayingCallback, questions_ibuttons
from loader import bot, db

router = Router()


async def generate_question(book_id, counter, call: types.CallbackQuery):
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
                text=f"{letter}", callback_data=f"question:{callback[0]}:{book_id}"
            )
        )
    builder.adjust(2, 2)

    await call.message.edit_text(
        text=f"{counter}. {questions[0]['question']}\n"
             f"{questions_text}",
        reply_markup=builder.as_markup()
    )


@router.message(F.text == "⚔️ Bellashuv")
async def uz_battle_main(message: types.Message):
    await message.answer(
        text="Savollar beriladigan kitob nomini tanlang",
        reply_markup=await battle_main_ibuttons(
            back_text="Ortga", back_callback="uz_back_battle_main"
        )
    )


@router.callback_query(F.data.startswith("table_"))
async def get_book_name(call: types.CallbackQuery):
    book_id = call.data.split("_")[1]
    await call.message.edit_text(
        text="Bellashuv turini tanlang", reply_markup=battle_ibuttons(
            random_opponent="Tasodifiy raqib bilan", offer_opponent="Raqib taklif qilish",
            playing_alone="Yakka o'yin", alone_callback="uz_alone",
            back="Ortga", back_callback="uz_back", book_id=book_id
        )
    )


@router.callback_query(F.data.startswith("book_id:"))
async def get_random_in_battle(call: types.CallbackQuery):
    book_id = call.data.split(':')[1]
    book_name_ = await db.select_book_by_id(id_=int(book_id))
    book_name = book_name_['table_name']
    user_id = call.from_user.id

    full_name = call.from_user.full_name

    numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']

    random_user = await db.select_user_random()

    markup = to_offer_ibuttons(
        agree_text="Qabul qilish", agree_id=user_id, refusal_text="Rad qilish", book_id=book_id
    )

    if random_user['telegram_id'] == user_id:
        other_random = await db.select_user_random()

        while other_random['telegram_id'] == random_user['telegram_id']:
            other_random = await db.select_user_random()

        await bot.send_message(
            chat_id=other_random['telegram_id'],
            text=f"Foydalanuvchi {full_name} Sizni {book_name} kitobi bo'yicha bellashuvga taklif qilmoqda!",
            reply_markup=markup
        )
    else:
        await bot.send_message(
            chat_id=random_user['telegram_id'],
            text=f"Foydalanuvchi {full_name} Sizni {book_name} kitobi bo'yicha bellashuvga taklif qilmoqda!",
            reply_markup=markup
        )
    await call.answer(
        text="Raqibingizga bellashuv taklifi yuborildi!"
    )
    for n in numbers:
        await call.message.edit_text(
            text=f"{n}"
        )
        await asyncio.sleep(1)
    await call.message.edit_text(
        text="Raqibingizdan javob kelmasa qayta <b>Tasodifiy raqib bilan</b> tugmasini bosing!"
    )


@router.callback_query(OfferCallback.filter())
async def get_opponent(call: types.CallbackQuery, callback_data: OfferCallback, state: FSMContext):
    opponent_id = str(callback_data.agree_id)
    book_id = int(callback_data.book_id)
    fullname = call.from_user.full_name
    user_id = call.from_user.id

    book_name = await db.select_book_by_id(id_=book_id)

    await bot.send_message(
        chat_id=opponent_id,
        text=f"Foydalanuvchi {fullname} {book_name['table_name']} kitobi bo'yicha bellashuvga rozilik bildirdi!",
        reply_markup=play_battle_ibuttons(
            start_text="Boshlash", user_id=str(user_id), book_id=book_id
        )
    )
    counter = 1
    await state.update_data(opponent=opponent_id, c=counter)

    await generate_question(book_id=book_id, counter=counter, call=call)


@router.callback_query(StartPlayingCallback.filter())
async def start_playing(call: types.CallbackQuery, callback_data: StartPlayingCallback, state: FSMContext):
    first_player = call.from_user.id
    second_player = callback_data.user_id
    book_id = callback_data.book_id

    first_check = await db.select_user(telegram_id=first_player)
    second_check = await db.select_user(telegram_id=second_player)

    if first_check['game_on'] is False and second_check['game_on'] is False:
        await db.update_gaming_status(telegram_id=first_player, status=True)
        await db.update_gaming_status(telegram_id=second_player, status=True)

        counter = 1

        await generate_question(
            book_id=book_id, counter=counter, call=call
        )
        await state.update_data(
            c=counter, opponent=second_player
        )


@router.callback_query(F.data.startswith("question:"))
async def get_question_answer(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    c = data['c']
    opponent_id = data['opponent']
    answer = call.data.split(":")[1]
    book_id = call.data.split(":")[2]
    user_id = call.from_user.id
    print(f"{opponent_id} opponent id")
    print(f"{user_id} user id")
    if c == 10:

        if answer == "a":
            await db.add_answer(telegram_id=user_id, question_number=c, correct_answer="✅")
        else:
            await db.add_answer(telegram_id=user_id, question_number=c, correct_answer="❌")

        await db.update_game_over(game_over=True, telegram_id=user_id)

        opponent_results = await db.select_answers_user(telegram_id=opponent_id)
        user_results = await db.select_answers_user(telegram_id=user_id)

        answer_number = str()
        answer_emoji = str()
        numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        for number in numbers:
            answer_number += f"{number} "
        print(f"{opponent_results} opponent results")
        print(f"{user_results} user results")
        if opponent_results and user_results is True:

            first_player = await db.select_answers_user(telegram_id=user_id)
            second_player = await db.select_answers_user(telegram_id=opponent_id)
            first_result = str()
            second_result = str()
        else:
            for result in user_results:
                answer_emoji += f"{result['correct_answer']} "

            await call.message.edit_text(
                text=f"Savollar tugadi!\n\nSizning natijangiz:\n\n"
                     f"{answer_number}\n\n{answer_emoji}\n\n"
                     f"Raqibingiz hozircha o'yinni yakunlamadi! Yakunlagach raqibingizni ham natijalari"
                     f"yuboriladi!"
            )

        await state.clear()

    else:
        c += 1
        await generate_question(
            book_id=book_id, counter=c, call=call
        )

        await state.update_data(
            c=c
        )

        if answer == "a":
            await db.add_answer(telegram_id=user_id, question_number=c - 1, correct_answer="✅")
        else:
            await db.add_answer(telegram_id=user_id, question_number=c - 1, correct_answer="❌")


@router.callback_query(F.data == "uz_back")
async def uz_back(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        text="Bosh sahifa", reply_markup=uz_start_buttons
    )
