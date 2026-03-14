import os
import asyncio

from dotenv import find_dotenv, load_dotenv

from aiogram import Dispatcher, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

load_dotenv(find_dotenv())

TOKEN = os.getenv("TOKEN")

dispatcher = Dispatcher()

@dispatcher.message(CommandStart())
async def mock_start_cmd(message: Message) -> None:
    await message.answer(f"Hello! {message.from_user.username}")

async def main() -> None:
    bot = Bot(token=TOKEN)
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())