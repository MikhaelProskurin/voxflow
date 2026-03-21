import os
import asyncio

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from aiogram import Dispatcher, Bot

from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from api.handlers.users import user_messages_router
from api.middleware.postgres import PostgresSessionMiddleware
from memory.database_engine import (
    async_session_factory,
    create_database_structure,
    drop_database_structure
)
# APSheduler

ALLOWED_UPDATES = [
    "message",
    "edited_message",
    "callback_query",
]

commands = []

dispatcher = Dispatcher()
dispatcher.include_router(user_messages_router)

bot = Bot(token=os.getenv("TOKEN"))


async def main() -> None:

    dispatcher.message.middleware(PostgresSessionMiddleware(session_factory=async_session_factory))
    dispatcher.callback_query.middleware(PostgresSessionMiddleware(session_factory=async_session_factory))
    await drop_database_structure()
    await create_database_structure()

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())
    await dispatcher.start_polling(bot, allowed_updates=ALLOWED_UPDATES)

if __name__ == "__main__":
    asyncio.run(main())
