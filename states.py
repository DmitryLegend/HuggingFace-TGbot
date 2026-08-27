from aiogram.fsm.state import State, StatesGroup


class GenStates(StatesGroup):
    """Состояние 'бот ждёт ввод (текст/фото/аудио) для выбранной задачи'.

    Какая именно задача выбрана — хранится в данных состояния (state.get_data()["task"]),
    а не отдельным State, чтобы не плодить по классу State на каждую из 10 задач.
    """

    waiting_for_input = State()
