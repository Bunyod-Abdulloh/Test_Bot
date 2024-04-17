from aiogram import Router, F, types

from handlers.users.uz.start import uz_start_buttons
from keyboards.inline.buttons import battle_ibuttons, battle_main_ibuttons
from loader import db

router = Router()


@router.message(F.text == "⚔️ Bellashuv")
async def uz_battle_main(message: types.Message):
    telegram_id = message.from_user.id

    # Users jadvalidan game_on ustunini FALSE holatiga tushirish
    await db.edit_status_users(
        game_on=False, telegram_id=telegram_id
    )

    # Results jadvalidan user ma'lumotlarini tozalash
    await db.delete_user_results(
        telegram_id=telegram_id
    )

    # Temporary answers jadvalidan user ma'lumotlarini tozalash
    await db.delete_answers_user(
        telegram_id=telegram_id
    )
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
            random_opponent="Tasodifiy raqib bilan", offer_opponent="Do'stni taklif qilish",
            playing_alone="Yakka o'yin", back="Ortga", back_callback="uz_back", book_id=book_id
        )
    )


@router.callback_query(F.data == "uz_back")
async def uz_back(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        text="Bosh sahifa", reply_markup=uz_start_buttons
    )
