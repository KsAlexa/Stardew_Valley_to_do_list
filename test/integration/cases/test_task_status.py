import pytest
from typing import Callable, List
import httpx
from helpers import assert_task_data
from service_client import ServiceClient
from src.api.handlers_models import *

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Завершить 1 задачу.
#     ОР: Cтатус поменялся на 'completed', задача переместилась в список выполненных задач, остальные параметры не изменились. Другая задача не изменилась.
def test_complete_task_manual(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)
    task_to_complete = initial_tasks[1]
    other_initial_task = [initial_tasks[0], initial_tasks[2]]

    completed_task = service_client.complete_task(task_to_complete.id)

    assert_task_data(
        completed_task,
        expected_id=task_to_complete.id,
        expected_name=task_to_complete.name,
        expected_type=task_to_complete.type,
        expected_status=TaskStatus.completed,
        expected_day_id=task_to_complete.day_id,
    )

    final_state = service_client.get_current_state()
    final_active_tasks = final_state.current_day_info.tasks
    completed_tasks = final_state.all_completed_tasks

    assert len(final_active_tasks) == len(other_initial_task)
    assert len(final_state.all_completed_tasks) == 1

    final_completed_task = completed_tasks[0]
    assert_task_data(
        final_completed_task,
        expected_id=task_to_complete.id,
        expected_name=task_to_complete.name,
        expected_type=task_to_complete.type,
        expected_status=TaskStatus.completed,
        expected_day_id=task_to_complete.day_id
    )

    other_final_active_task = [task for task in final_active_tasks if task.id in {task.id for task in other_initial_task}]
    other_initial_task.sort(key=lambda task: task.id)
    other_final_active_task.sort(key=lambda task: task.id)

    assert other_final_active_task == other_initial_task

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Перелистнуть день.
#     ОР: Cтатусы поменялись на 'completed', задачи переместились в список выполненных задач, остальные параметры не изменились, в текущем дне нет задач.
def test_complete_task_automatically(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)

    state_after_switch = service_client.set_next_day()

    assert len(state_after_switch.current_day_info.tasks) == 0

    completed_tasks = state_after_switch.all_completed_tasks
    assert len(completed_tasks) == len(initial_tasks)

    completed_tasks.sort(key=lambda task: task.id)
    initial_tasks.sort(key=lambda task: task.id)

    for completed, initial in zip(completed_tasks, initial_tasks):
        assert_task_data(
            completed,
            expected_id=initial.id,
            expected_name=initial.name,
            expected_type=initial.type,
            expected_status=TaskStatus.completed,
            expected_day_id=initial.day_id
        )

# 1. Создать дефолтный день с 2мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 2 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Завершить обе задачи.
#     ОР: Cтатус поменялся на 'completed', задачи переместились в список выполненных задач, остальные параметры не изменились.
# 3. Пометить 1 задачу как активную.
#     ОР: Cтатус поменялся на 'active', задача переместилась в текущий день, остальные параметры не изменились. Другая завершенная задача не изменилась.
def test_make_completed_task_active(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)
    task_to_activate = initial_tasks[1]
    other_initial_tasks = [initial_tasks[0], initial_tasks[2]]

    for task in initial_tasks:
        service_client.complete_task(task.id)

    activated_task = service_client.activate_task(task_to_activate.id)

    assert_task_data(
        activated_task,
        expected_id=task_to_activate.id,
        expected_name=task_to_activate.name,
        expected_type=task_to_activate.type,
        expected_status=TaskStatus.active,
        expected_day_id=task_to_activate.day_id,
    )

    final_state = service_client.get_current_state()

    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == len(initial_tasks) - 1

    active_task = final_state.current_day_info.tasks[0]
    assert_task_data(
        active_task,
        expected_id=task_to_activate.id,
        expected_name=task_to_activate.name,
        expected_type=task_to_activate.type,
        expected_status=TaskStatus.active,
        expected_day_id=task_to_activate.day_id
    )

    other_final_completed_tasks = final_state.all_completed_tasks
    other_final_completed_tasks.sort(key=lambda task: task.id)
    other_initial_tasks.sort(key=lambda task: task.id)  

    for completed, initial in zip(other_final_completed_tasks, other_initial_tasks):
        assert_task_data(
        completed,
        expected_id=initial.id,
        expected_name=initial.name,
        expected_type=initial.type,
        expected_status=TaskStatus.completed,
        expected_day_id=initial.day_id
    )

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Завершить несуществующую задачу.
#     ОР: Возвращается ошибка 404 TaskNotFoundException: 'Task with id "{task.id}" not found. Задач в текущем дне нет, Задач в списке выполненных задач нет.
def test_complete_nonexistent_task_should_fail(service_client: ServiceClient, default_day_state: CurrentStateResponse):
    non_existent_id = 88

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.complete_task(non_existent_id)

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
# 2. Завершить задачу.
#     ОР: Cтатус поменялся на 'completed', задача переместилась в список выполненных задач, остальные параметры не изменились.
# 3. Переименовать завершенную задачу.
#     ОР: Возвращается ошибка 400 InvalidTaskStateException: 'Task with ID {id} is completed. To edit it, make it active first'. Задача не изменилась. Задач в текущем дне нет.
def test_rename_completed_task_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]

    service_client.complete_task(initial_task.id)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        request = TaskNameRequest(name='Новое имя')
        service_client.rename_task(initial_task.id, request)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with ID {initial_task.id} is completed. To edit it, make it active first.'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 1

    completed_task = final_state.all_completed_tasks[0]
    assert_task_data(
        completed_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=TaskStatus.completed,
        expected_day_id=initial_task.day_id,
    )

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Завершить задачу.
#     ОР: Cтатус поменялся на 'completed', задача переместилась в список выполненных задач, остальные параметры не изменились.
# 3. Сделать задачу daily
#     ОР: Возвращается ошибка 400 InvalidTaskStateException: 'Task with ID {id} is completed. To make it a daily task, make it active first.'. Задача не изменилась.
def test_make_completed_task_daily_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]
    service_client.complete_task(initial_task.id)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.make_task_daily(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == (
        f'Task with ID {initial_task.id} is completed. To make it a daily task, make it active first'
    )

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 1

    completed_task = final_state.all_completed_tasks[0]
    assert_task_data(
        completed_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=TaskStatus.completed,
        expected_day_id=initial_task.day_id,
    )

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Завершить задачу.
#     ОР: Cтатус поменялся на 'completed', задача переместилась в список выполненных задач, остальные параметры не изменились.
# 3. Сделать задачу one-time
#     ОР: Возвращается ошибка 400 InvalidTaskStateException: 'Task with ID {id} is completed.'. Задача не изменилась.
def test_make_completed_task_one_time_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]
    service_client.complete_task(initial_task.id)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.make_task_one_time(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with ID {initial_task.id} is completed.'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 1

    completed_task = final_state.all_completed_tasks[0]
    assert_task_data(
        completed_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=TaskStatus.completed,
        expected_day_id=initial_task.day_id,
    )

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Завершить задачу.
#     ОР: Cтатус поменялся на 'completed', задача переместилась в список выполненных задач, остальные параметры не изменились.
# 3. Завершить завершенную задачу
#     ОР: Возвращается ошибка 400 InvalidTaskStateException: 'Task with ID {id} is already completed.'. Pадача не изменилась.
def test_complete_completed_task_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]
    service_client.complete_task(initial_task.id)

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.complete_task(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with ID {initial_task.id} is already completed.'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 1

    completed_task = final_state.all_completed_tasks[0]
    assert_task_data(
        completed_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=TaskStatus.completed,
        expected_day_id=initial_task.day_id,
    )

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Завершить задачу.
#     ОР: Cтатус поменялся на 'completed', задача переместилась в список выполненных задач, остальные параметры не изменились.
# 3. Сделать активной несуществующую задачу.
#     ОР: Возвращается ошибка 404 TaskNotFoundException: 'Task with id "{task.id}" not found. В текущем дне нет задач. Завершенная задача не изменилась.
def test_make_active_nonexistent_task_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]
    service_client.complete_task(initial_task.id)

    non_existent_id = 88
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.activate_task(non_existent_id)

    response = exc_info.value.response
    assert response.status_code == 404

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with id {non_existent_id} not found'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 1

    completed_task = final_state.all_completed_tasks[0]
    assert_task_data(
        completed_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=TaskStatus.completed,
        expected_day_id=initial_task.day_id,
    )

# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Сделать задачу активной.
#     ОР: Возвращается ошибка 400 InvalidTaskStateException: 'Task with ID {id} is already active.'.
def test_make_active_task_active_should_fail(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task = task_factory(1)[0]

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        service_client.activate_task(initial_task.id)

    response = exc_info.value.response
    assert response.status_code == 400

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with ID {initial_task.id} is already active.'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0

    final_task = final_state.current_day_info.tasks[0]
    assert_task_data(
        final_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=TaskStatus.active,
        expected_day_id=initial_task.day_id,
    )

