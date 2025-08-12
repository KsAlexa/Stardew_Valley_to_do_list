import pytest
from typing import Callable, List
import httpx
from helpers import assert_task_data
from service_client import ServiceClient
from src.api.handlers_models import *

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Сделать одну задачу daily
#     ОР: тип задачи изменен, остальные параметры не изменились. Другая задача не изменилась. Задач в списке выполненных задач нет.
def test_make_one_time_task_daily(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)
    task_to_make_daily = initial_tasks[1]
    other_initial_tasks = [initial_tasks[0], initial_tasks[2]]

    daily_task = service_client.make_task_daily(task_to_make_daily.id)

    assert_task_data(
        daily_task,
        expected_id=task_to_make_daily.id,
        expected_name=task_to_make_daily.name,
        expected_type=TaskType.daily,
        expected_status=task_to_make_daily.status,
        expected_day_id=task_to_make_daily.day_id,
    )

    final_state = service_client.get_current_state()
    
    assert len(final_state.all_completed_tasks) == 0
    assert len(final_state.current_day_info.tasks) == len(initial_tasks)

    final_active_tasks = final_state.current_day_info.tasks
    final_daily_task = next(task for task in final_active_tasks if task.id == task_to_make_daily.id)
    assert_task_data(
        final_daily_task,
        expected_id=task_to_make_daily.id,
        expected_name=task_to_make_daily.name,
        expected_type=TaskType.daily,
        expected_status=task_to_make_daily.status,
        expected_day_id=task_to_make_daily.day_id,
    )

    other_final_tasks = [task for task in final_active_tasks if task.id in {t.id for t in other_initial_tasks}]
    assert other_final_tasks == other_initial_tasks

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Изменить типы задач на 'daily'
#     ОР: Типы поменялись на 'daily', остальные параметры не изменились. Задач в списке выполненных задач нет.
# 3. Перелистнуть день.
#     ОР: Задачи не изменились. Задач в списке выполненных задач нет.
def test_daily_tasks_remain_when_change_day(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)

    for task in initial_tasks:
        service_client.make_task_daily(task.id)

    current_state = service_client.get_current_state()

    assert len(current_state.current_day_info.tasks) == len(initial_tasks)
    assert len(current_state.all_completed_tasks) == 0

    state_after_switch = service_client.set_next_day()
    new_day_id = state_after_switch.current_day_info.id
    final_daily_tasks = state_after_switch.current_day_info.tasks

    assert len(final_daily_tasks) == len(initial_tasks)
    assert len(state_after_switch.all_completed_tasks) == 0


    for final_task, initial_task in zip(final_daily_tasks, initial_tasks):
        assert_task_data(
            final_task,
            expected_id=initial_task.id,
            expected_name=initial_task.name,
            expected_type=TaskType.daily,
            expected_status=initial_task.status,
            expected_day_id=new_day_id,
        )

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Изменить типы задач на 'daily'
#     ОР: Типы поменялись на 'daily', остальные параметры не изменились. Задач в списке выполненных задач нет.
#  3. Переименовать 1 задачу.
#     ОР: Задача переименована, остальные параметры не изменились. Другая задача не изменилась. Задач в списке выполненных задач нет.
def test_rename_daily_task(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)
    task_to_rename = initial_tasks[1]
    other_initial_tasks = [initial_tasks[0], initial_tasks[2]]
    new_name = 'Новое имя ежедневной задачи'

    for task in initial_tasks:
        service_client.make_task_daily(task.id)

    updated_task = service_client.rename_task(task_to_rename.id, TaskNameRequest(name=new_name))
    assert_task_data(
        updated_task,
        expected_id=task_to_rename.id,
        expected_name=new_name,
        expected_type=TaskType.daily,
        expected_status=task_to_rename.status,
        expected_day_id=task_to_rename.day_id,
    )

    final_state = service_client.get_current_state()
    final_active_tasks = final_state.current_day_info.tasks

    assert len(final_state.all_completed_tasks) == 0
    assert len(final_state.current_day_info.tasks) == len(initial_tasks)

    final_renamed_task = next(task for task in final_active_tasks if task.id == task_to_rename.id)
    assert_task_data(
        final_renamed_task,
        expected_id=task_to_rename.id,
        expected_name=new_name,
        expected_type=TaskType.daily,
        expected_status=task_to_rename.status,
        expected_day_id=task_to_rename.day_id,
    )

    other_final_tasks = [task for task in final_active_tasks if task.id in {task.id for task in other_initial_tasks}]
    for final_task, initial_task in zip(other_final_tasks, other_initial_tasks):
        assert_task_data(
            final_task,
            expected_id=initial_task.id,
            expected_name=initial_task.name,
            expected_type=TaskType.daily,
            expected_status=initial_task.status,
            expected_day_id=initial_task.day_id,
        )

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factыory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Изменить типы задач на 'daily'
#     ОР: Типы поменялись на 'daily', остальные параметры не изменились. Задач в списке выполненных задач нет.
# 3. Изменить тип одной задача на one-time.
#    ОР: Задача поменяла свой тип, остальные параметры не изменились, вторая задача не изменилась. Задач в списке выполненных задач нет.
def test_make_daily_task_one_time(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)
    task_to_make_one_time = initial_tasks[1]
    other_initial_tasks = [initial_tasks[0], initial_tasks[2]]
    
    for task in initial_tasks:
        service_client.make_task_daily(task.id)

    updated_task = service_client.make_task_one_time(task_to_make_one_time.id)
    assert_task_data(
        updated_task,
        expected_id=task_to_make_one_time.id,
        expected_name=task_to_make_one_time.name,
        expected_type=TaskType.one_time,
        expected_status=task_to_make_one_time.status,
        expected_day_id=task_to_make_one_time.day_id,
    )

    final_state = service_client.get_current_state()
    final_active_tasks = final_state.current_day_info.tasks
    assert len(final_state.all_completed_tasks) == 0
    assert len(final_state.current_day_info.tasks) == len(initial_tasks)

    final_updated_task = next(task for task in final_active_tasks if task.id == task_to_make_one_time.id)
    assert_task_data(
        final_updated_task,
        expected_id=task_to_make_one_time.id,
        expected_name=task_to_make_one_time.name,
        expected_type=TaskType.one_time,
        expected_status=task_to_make_one_time.status,
        expected_day_id=task_to_make_one_time.day_id,
    )

    other_final_tasks = [task for task in final_active_tasks if task.id in {task.id for task in other_initial_tasks}]
    for final_task, initial_task in zip(other_final_tasks, other_initial_tasks):
        assert_task_data(
            final_task,
            expected_id=initial_task.id,
            expected_name=initial_task.name,
            expected_type=TaskType.daily,
            expected_status=initial_task.status,
            expected_day_id=initial_task.day_id,
        )

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Сделать daily несуществующую задачу.
#     ОР: Возвращается ошибка 404 TaskNotFoundException: 'Task with id "{task.id}" not found. Задач в текущем дне нет, Задач в списке выполненных задач нет.
def test_make_daily_nonexistent_task_should_fail(service_client: ServiceClient, default_day_state: CurrentStateResponse):
    non_existent_id = 88

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.make_task_daily(non_existent_id)

    response = exc_info.value.response
    assert response.status_code == 404

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with id {non_existent_id} not found'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 0

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Изменить тип задачи на 'daily'
#     ОР: Тип поменялся на 'daily', остальные параметры не изменились. Задач в списке выполненных задач нет.
#  3. Завершить задачу.
#     ОР: Возвращается ошибка 400 'Task with ID {id} is completed. To make it a daily task, make it active first'. Задача не изменилась, Задач в списке выполненных задач нет.
def test_complete_daily_task_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]
    service_client.make_task_daily(initial_task.id)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.complete_task(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == (
        f"Task with ID {initial_task.id} cannot be completed. Only 'one-time' tasks can be marked as completed"
    )

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0

    final_task = final_state.current_day_info.tasks[0]
    assert_task_data(
        final_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=TaskType.daily,
        expected_status=initial_task.status,
        expected_day_id=initial_task.day_id,
    )

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Изменить тип задачи на 'daily'
#     ОР: Тип поменялся на 'daily', остальные параметры не изменились. Задач в списке выполненных задач нет.
#  3. Сделать задачу еще раз daily
#     ОР: Возвращается ошибка 400 'Task with ID {id} is already a daily task.' Задача не изменилась, Задач в списке выполненных задач нет.
def test_make_daily_task_daily_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]
    service_client.make_task_daily(initial_task.id)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.make_task_daily(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with ID {initial_task.id} is already a daily task.'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0

    final_task = final_state.current_day_info.tasks[0]
    assert_task_data(
        final_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=TaskType.daily,
        expected_status=initial_task.status,
        expected_day_id=initial_task.day_id,
    )

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Сделать one-time несуществующую задачу.
#     ОР: Возвращается ошибка 404 TaskNotFoundException: 'Task with id "{task.id}" not found. Задач в текущем дне нет, Задач в списке выполненных задач нет.
def test_make_one_time_nonexistent_task_should_fail(service_client: ServiceClient, default_day_state: CurrentStateResponse):
    non_existent_id = 88

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.make_task_one_time(non_existent_id)

    response = exc_info.value.response
    assert response.status_code == 404

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with id {non_existent_id} not found'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 0

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
#  2. Сделать задачу еще раз one-time
#     ОР: Возвращается ошибка 400 Task with ID {id} is already a one-time task. Задача не изменилась, Задач в списке выполненных задач нет.
def test_make_one_time_task_one_time_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.make_task_one_time(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with ID {initial_task.id} is already a one-time task.'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0

    final_task = final_state.current_day_info.tasks[0]
    assert_task_data(
        final_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=TaskType.one_time,
        expected_status=initial_task.status,
        expected_day_id=initial_task.day_id,
    )