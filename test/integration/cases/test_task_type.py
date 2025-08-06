
# def test_make_one_time_task_daily()

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать 2 задачи.
#     ОР: Задачи созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню.
# 3. Изменить тип задач на 'daily'.
#     ОР: Типы поменялись на 'daily', остальные параметры не изменились.
# 4. Переименовать 1 задачу.
#     ОР: Задача переименована, остальные параметры не поменялись, вторая задача не изменилась.
# 4. Перелистнуть день.
#     ОР: Задачи не изменились
# def test_daily_tasks_remain_when_change_day():

#def test_rename_daily_task():

#def test_make_daily_nonexistent_task_should_fail():

#def test_complete_daily_task_should_fail():

#def test_make_daily_task_daily_should_fail():

#def test_make_daily_task_one_time()

#def test_make_one_time_nonexistent_task_should_fail()

#def test_make_one_time_task_one_time_should_fail()