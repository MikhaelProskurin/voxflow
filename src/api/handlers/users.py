import pendulum
import dateparser
from dateparser.search import search_dates
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from memory.schemas import User, Task
from agentic.core import create_voxflow_agent, VoxflowAgent, ExtractedTasksModel, TaskModel
from api.keyboards import tasks_confirmation_keyboard

tz = pendulum.timezone("Europe/Moscow")
user_messages_router = Router()

def extract_deadlines(content: ExtractedTasksModel) -> list[datetime | None]:
    kwargs = {
        "RELATIVE_BASE": datetime.now(tz), 
        "PREFER_DATES_FROM": "future"
    }
    extracted = [search_dates(t.due_date, languages=["ru"], settings=kwargs) for t in content]
    results = [date[0][1] if date else None for date in extracted]
    return results

@user_messages_router.message(CommandStart())
async def command_start(message: Message, session: AsyncSession) -> None:
    idx, username = message.from_user.id, message.from_user.username

    select_statement = select(User).where(User.telegram_user_id == idx)
    insert_statement = insert(User).values((idx, username))

    result = await session.execute(select_statement)
    user = result.fetchone()

    if not user:
        await session.execute(insert_statement)
        await session.commit()
        await message.answer(f"{username}, Welcome to Voxflow!")
        return
    else:
        await message.answer(f"{username}, welcome back!")


class ExtractTasks(StatesGroup):
    confirmation = State()

@user_messages_router.message(F.text | F.voice)
async def process_user_input(message: Message, state: FSMContext, bot: Bot) -> None:
    agent: VoxflowAgent = create_voxflow_agent()

    if message.text and not message.voice:
        text = message.text

    elif message.voice:
        audio_data = await bot.download(message.voice.file_id)
        text = await agent.transcribe(audio_data=audio_data)

    extracted_data: ExtractedTasksModel = await agent.extract_tasks_from_text(text)

    if data:= extracted_data.content:
        deadlines = extract_deadlines(data)
        titles = [item.title for item in data]

        await state.update_data(
            tasks=[item.model_dump() for item in data],
            deadlines=deadlines
        )
        await message.answer("Can you confirm the tasks?", reply_markup=tasks_confirmation_keyboard(titles, deadlines))
        await state.set_state(ExtractTasks.confirmation)

@user_messages_router.callback_query(ExtractTasks.confirmation, F.data.startswith("task:confirm:"))
async def confirm_task(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    idx = int(callback.data.split(":")[-1])
    data = await state.get_data()

    tasks: list[dict] = data.get("tasks", [])
    deadlines: list[datetime | None] = data.get("deadlines", [])
    confirmed: list[int] = data.get("confirmed", [])

    if idx in confirmed:
        await callback.answer("Already confirmed.")
        return

    task_data = tasks[idx]
    await session.execute(
        insert(Task).values(
            telegram_user_id=callback.from_user.id,
            title=task_data["title"],
            status="opened",
            due_date=deadlines[idx],
        )
    )
    await session.commit()

    confirmed.append(idx)
    await state.update_data(confirmed=confirmed)

    titles = [t["title"] for t in tasks]
    remaining = set(range(len(tasks))) - set(confirmed)

    if not remaining:
        await state.clear()
        await callback.message.edit_text("All tasks saved!")
        await callback.answer()
        return

    updated_keyboard = tasks_confirmation_keyboard(
        titles=titles,
        deadlines=deadlines,
        exclude_indices=set(confirmed),
    )
    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    await callback.answer("Task confirmed!")
