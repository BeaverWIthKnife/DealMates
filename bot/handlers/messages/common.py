from aiogram import F, Router, Bot, Dispatcher
from aiogram.types import Message, User, Chat, FSInputFile, CallbackQuery, InlineQuery, InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ChatType, ContentType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.formatting import as_numbered_list

from contextlib import suppress
from hashlib import md5

from states import States
from utils import Category, Lobby, LobbyModel, merge_product_info

for prod in Category.products("", ""):
    Lobby.create_lobby(prod)

async def safe_message_delete(bot: Bot, chat_id: int, menu_id: int | None):
    if not menu_id:
        return
    
    with suppress(TelegramBadRequest):
        await bot.delete_message(
            chat_id,
            menu_id
        )

async def send_category_search_menu(bot: Bot, chat_id: int, menu_id: int | None, state: FSMContext):
    data = await state.get_data()
    await safe_message_delete(bot, chat_id, menu_id or data.get("menu_id"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔎 Пошук категорії",
            switch_inline_query_current_chat=""
        )]
    ])

    menu = await bot.send_message(
        chat_id, (
            "🏪 Оберіть категорію продукту"
        ), reply_markup=kb
    )

    await state.update_data(menu_id=menu.message_id)


async def send_lobby_search_menu(bot: Bot, chat_id: int, menu_id: int | None, state: FSMContext):
    data = await state.get_data()
    await safe_message_delete(bot, chat_id, menu_id or data.get("menu_id"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔎 Обрати продукт",
            switch_inline_query_current_chat=""
        )],
        [InlineKeyboardButton(
            text="‹ Назад",
            callback_data="menu"
        )]
    ])

    menu = await bot.send_message(
        chat_id, (
            f"🏪 Вибір продуктів у категорії {data['category']}"
        ), reply_markup=kb
    )

    await state.update_data(menu_id=menu.message_id)


async def send_lobby_menu(bot: Bot, chat_id: int, menu_id: int | None, state: FSMContext):
    data = await state.get_data()
    await safe_message_delete(bot, chat_id, menu_id or data.get("menu_id"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧺",
                callback_data="amount"
            ),
            InlineKeyboardButton(
                text="✅",
                callback_data="changeStatus"
            ),
            InlineKeyboardButton(
                text="💳",
                callback_data="pay"
            ),
            InlineKeyboardButton(
                text="❓",
                callback_data="faq"
            )
        ],
        [InlineKeyboardButton(
            text="‹ Вийти",
            callback_data="menu"
        )]
    ])

    lobby = Lobby.get_lobby(data['product'])
    product = Category.products(data['category'], data['product'])[0]
    users = [f"{user.id} {user.status}({user.wants})" for user in lobby.users]

    menu = await bot.send_message(
        chat_id, (
            f"🏪 {data['product']} / {data['category']}\n\n"
            "Користувачі:\n"
            f"{as_numbered_list(*users).as_html()}\n\n"
            f"╔ Звичайна ціна: {lobby.common_price}грн/{lobby.unit}\n"
            f"╠ ═ Опт {product.bulks[0].range[0]}-{product.bulks[0].range[1]}/{product.unit} {product.bulks[0].unit_price}грн\n"
            f"╠ ═ Опт {product.bulks[1].range[0]}-{product.bulks[1].range[1]}/{product.unit} {product.bulks[1].unit_price}грн\n"
            f"╚ ⚡ <b>Ціна зараз: {lobby.bulk}грн/{lobby.unit}</b>\n\n"
            "❓ — Допомога"
        ), reply_markup=kb, parse_mode="HTML"
    )

    await state.update_data(menu_id=menu.message_id, lobby=data['product'])


async def leave_lobby(id: int, product: str, bot: Bot, dp: Dispatcher):
    Lobby.remove_user(id, product)

    lobby = Lobby.get_lobby(product)
    await resend_lobby_menu(id, lobby, bot, dp)


async def resend_lobby_menu(user_id: int | None, lobby: LobbyModel, bot: Bot, dp: Dispatcher):
    for user in lobby.users:
        if user_id and user.id == user_id:
            continue
        user_state = dp.fsm.get_context(bot, user.chat_id, user.id)
        await send_lobby_menu(bot, user.chat_id, None, user_state)


router = Router()


@router.callback_query(F.data == "amount", StateFilter(States.in_lobby))
async def amount_callback(
    callback_query: CallbackQuery, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    await state.set_state(States.amount_input)
    await callback_query.answer("🧺 Вкажіть нову кількість до придбання", show_alert=True)


@router.message(StateFilter(States.amount_input))
async def new_amount_message(
    message: Message, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    if not message.text.isdigit():
        await message.answer("❌ Вкажіть числове значення")
        return
    
    await message.delete()
    data = await state.get_data()
    Lobby.set_user(
        event_from_user.id, 
        data["product"], 
        "wants", 
        int(message.text)
    )
    lobby = Lobby.get_lobby(data['product'])
    bulk = Lobby.get_bulk(data['category'], data['product'], lobby)
    Lobby.set_lobby(
        data['product'],
        "bulk",
        bulk
    )

    await state.set_state(States.in_lobby)
    
    lobby = Lobby.get_lobby(data["product"])
    await resend_lobby_menu(
        None,
        lobby,
        bot,
        dispatcher
    )


@router.message(F.via_bot, StateFilter(States.category_search))
async def on_category_sent(
    message: Message, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    bot: Bot
):
    await message.delete()
    await state.set_state(States.lobby_search)
    await state.update_data(category=message.text)
    await send_lobby_search_menu(
        bot,
        event_chat.id,
        None,
        state
    )


@router.message(F.via_bot, StateFilter(States.lobby_search))
async def on_product_sent(
    message: Message, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    await message.delete()
    prod = message.text
    await state.set_state(States.in_lobby)
    await state.update_data(product=prod)

    Lobby.add_user(
        event_from_user.id,
        prod,
        event_chat.id
    )

    await send_lobby_menu(
        bot,
        event_chat.id,
        None,
        state
    )

    lobby = Lobby.get_lobby(prod)
    await resend_lobby_menu(event_from_user.id, lobby, bot, dispatcher)


@router.inline_query(StateFilter(States.lobby_search))
async def on_lobby_search_query(inline_query: InlineQuery, state: FSMContext):
    query = inline_query.query
    data = await state.get_data()
    products = Category.products("" or data.get("category"), query)

    results = []
    for prod in products:
        prod_info = merge_product_info(prod)
        results.append(InlineQueryResultArticle(
            id=md5(prod.title.encode()).hexdigest(),
            title=prod_info["title"],
            description=prod_info["description"],
            input_message_content=InputTextMessageContent(
                message_text=prod.title
            ),
            thumbnail_url=prod.url if prod.url else None
        ))
    
    await inline_query.answer(results=results, is_personal=True, cache_time=0)


@router.inline_query(StateFilter(States.category_search))
async def on_category_search_query(inline_query: InlineQuery, state: FSMContext):
    query = inline_query.query
    categories = Category.get(query)
    
    results = []
    for cat in categories:
        results.append(InlineQueryResultArticle(
            id=md5(cat.title.encode()).hexdigest(),
            title=cat.title,
            description=f"{cat.products} шт.",
            input_message_content=InputTextMessageContent(
                message_text=cat.title
            ),
        ))

    await inline_query.answer(results=results, is_personal=True, cache_time=0)


@router.callback_query(F.data == "changeStatus")
async def change_status_callback(
    callback_query: CallbackQuery, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    await callback_query.answer()
    data = await state.get_data()
    
    Lobby.set_user(
        event_from_user.id,
        data["product"],
        "status",
        "✅"
    )

    lobby = Lobby.get_lobby(data["product"])
    await resend_lobby_menu(
        None,
        lobby,
        bot,
        dispatcher
    )


@router.callback_query(F.data == "pay")
async def pay_callback(
    callback_query: CallbackQuery, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    await callback_query.answer()
    data = await state.get_data()
    
    Lobby.set_user(
        event_from_user.id,
        data["product"],
        "status",
        "💳"
    )

    lobby = Lobby.get_lobby(data["product"])
    await resend_lobby_menu(
        None,
        lobby,
        bot,
        dispatcher
    )


@router.callback_query(F.data == "faq")
async def pay_callback(
    callback_query: CallbackQuery, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    await callback_query.answer((
        "🕑 — Очікування\n"
        "✅ — Готовність оплати\n"
        "💳 — Оплачено\n\n"
        "🧺 — Змінити к-ть бажаного продукту\n"
        "✅ — Змінити статус на «Хочу оплатити»\n"
        "💳 — Оплатити рахунок"
    ), show_alert=True)


@router.callback_query(F.data == "menu")
async def leave_callback(
    callback_query: CallbackQuery, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    data = await state.get_data()
    if lobby := data.get("lobby"):
        print("Remind me to leave from lobby, please.")
        await leave_lobby(event_from_user.id, data["product"], bot, dispatcher)
    await state.set_state(States.category_search)
    await state.update_data(lobby=None)
    await send_category_search_menu(
        bot,
        event_chat.id,
        None,
        state
    )

@router.message(Command("start"))
async def on_start_command(
    message: Message, 
    state: FSMContext, 
    event_from_user: User,
    event_chat: Chat,
    dispatcher: Dispatcher,
    bot: Bot
):
    # if event_from_user.id not in {1064586259, 1464020901, 723985449, 1052870053, 717093143}:
    #     await message.answer("Not 4 u, sorry ;(")
    #     return
    await message.delete()
    data = await state.get_data()
    if lobby := data.get("lobby"):
        print("Remind me to leave from lobby, please.")
        await leave_lobby(event_from_user.id, data["product"], bot, dispatcher)
    await state.set_state(States.category_search)
    await state.update_data(lobby=None)
    await send_category_search_menu(
        bot,
        event_chat.id,
        None,
        state
    )

@router.message(F.photo)
async def catch_photo(message: Message):
    text = (
        f"file_id: {message.photo[-1].file_id}\n"
        f"file_unique_id: {message.photo[-1].file_unique_id}"
    )
    await message.reply(text)