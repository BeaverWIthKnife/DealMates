from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

import os
import asyncio
import logging

from handlers.messages import common


logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot("", parse_mode="HTML")
    dp = Dispatcher()

    dp.include_routers(
        common.router
    )

    await bot.set_my_commands([
        BotCommand(command="start", description="Invoke main menu")
    ])

    await dp.start_polling(bot)
    

asyncio.run(main())