import pytest
from helpers import assert_task_data
from service_client import ServiceClient
from src.api.handlers_models import *
from typing import Callable, List, cast
import requests
import httpx


# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: Получен дефолтный день, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать 3 задачи. 
#     ОР: 3 задачи созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 3. Получить текущий день.
#     ОР: Задач в текущем дне 3, Задач в списке выполненных задач нет
def test_create_tasks(service_client: ServiceClient, default_day_state: CurrentStateResponse):
    task_names_list = ['Тестовая задача 1', 'Тестовая задача 2', 'Тестовая задача 3']
    current_day = default_day_state.current_day_info

    created_tasks: List[TaskResponse] = []
    for task_name in task_names_list:
        request = TaskNameRequest(name=task_name)
        new_task = service_client.create_task(request)

        assert new_task.name == task_name
        assert new_task.type == TaskType.one_time
        assert new_task.status == TaskStatus.active
        assert new_task.day_id == current_day.id
        created_tasks.append(new_task)

    final_state = service_client.get_current_state()
    final_active_tasks = final_state.current_day_info.tasks
    assert len(final_active_tasks) == len(task_names_list)
    assert len(final_state.all_completed_tasks) == 0

    assert created_tasks == final_active_tasks


# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Переименовать одну задачу.
#     ОР: Задача переименована, остальные ее параметры не поменялись
# 3. Получить текущий день.
#     ОР: Задач в списке выполненных задач нет, Задач в текущем дне 3, переименованная задача имеет новое имя, остальные задачи не изменились

def test_rename_task(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(3)
    task_to_rename = initial_tasks[1]
    new_task_name = 'Новое имя 2-й задачи'
    other_initial_tasks = [initial_tasks[0], initial_tasks[2]]

    rename_request = TaskNameRequest(name=new_task_name)
    renamed_task = service_client.rename_task(task_to_rename.id, rename_request)

    assert_task_data(
        renamed_task,
        expected_id=task_to_rename.id,
        expected_name=new_task_name,
        expected_type=task_to_rename.type,
        expected_status=task_to_rename.status,
        expected_day_id=task_to_rename.day_id
    )

    final_state = service_client.get_current_state()
    final_active_tasks = final_state.current_day_info.tasks
    completed_tasks = final_state.all_completed_tasks

    assert len(final_active_tasks) == len(initial_tasks)
    assert len(completed_tasks) == 0

    final_renamed_task = next((task for task in final_active_tasks if task.id == task_to_rename.id), None)
    assert final_renamed_task is not None
    assert_task_data(
        final_renamed_task,
        expected_id=task_to_rename.id,
        expected_name=new_task_name,
        expected_type=task_to_rename.type,
        expected_status=task_to_rename.status,
        expected_day_id=task_to_rename.day_id
    )

    other_final_active_tasks = [task for task in final_active_tasks if task.id in {task.id for task in other_initial_tasks}]
    assert other_final_active_tasks == other_initial_tasks


# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу с пустым именем. Создать задачу только с пробелом.
#     ОР: Задача не создана, возвращается ошибка 422 ValidationError (или Unprocessable Entity?): 'Task name must have at least 1 character'. Задач в текущем дне нет, Задач в списке выполненных задач нет
@pytest.mark.parametrize('empty_name', ['', ' ', '\t', '\n', '  \t  \n  '])
def test_create_task_with_empty_name_should_fail(service_client: ServiceClient, default_day_state: CurrentStateResponse,
                                                 empty_name: str):
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        payload = {'name': empty_name}
        service_client.create_task(cast(TaskNameRequest, payload))

    response = exc_info.value.response
    assert response.status_code == 422

    error_detail = response.json()
    assert 'detail' in error_detail
    assert any('Task name must have at least 1 character' in detail.get('msg', '') for detail in error_detail['detail'])

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 0


# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Создать задачу с таким же именем.
#     ОР: Задача не создана, возвращается ошибка 409 DuplicateTaskNameException: 'Task with name "{task.name}" already exists'. Существующая задача не изменилась, Задач в текущем дне нет, Задач в списке выполненных задач нет
def test_create_task_with_duplicate_name_should_fail(service_client: ServiceClient,
                                                     task_factory: Callable[[int], TaskResponse]):
    initial_task_list = task_factory(1)
    initial_task = initial_task_list[0]
    existing_name = initial_task.name

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        request = TaskNameRequest(name=existing_name)
        service_client.create_task(request)

    response = exc_info.value.response
    assert response.status_code == 409

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with name "{existing_name}" already exists'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0

    final_task = final_state.current_day_info.tasks[0]
    assert_task_data(
        final_task,
        expected_id=initial_task.id,
        expected_name=existing_name,
        expected_type=initial_task.type,
        expected_status=initial_task.status,
        expected_day_id=initial_task.day_id
    )


# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Поменять имя несуществующей задачи.
#     ОР: Задача не создана, возвращается ошибка 404 EntityNotFound: 'Task with id "{task.id}" not found', Задач в текущем дне нет, Задач в списке выполненных задач нет
def test_rename_nonexistent_task_should_fail(service_client: ServiceClient, default_day_state: CurrentStateResponse):
    name = 'Имя задачи'
    task_id = 88
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        request = TaskNameRequest(name=name)
        service_client.rename_task(task_id, request)

    response = exc_info.value.response
    assert response.status_code == 404

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with id {task_id} not found'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 0
    assert len(final_state.all_completed_tasks) == 0


# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Поменять имя задачи на пустую строку. Поменять имя задачи на пробел.
#     ОР: Задача не создана, возвращается ошибка 422 ValidationError (или Unprocessable Entity?): 'Task name must have at least 1 character', существующая задача не изменилась, Задач в списке выполненных задач нет
@pytest.mark.parametrize("empty_name", ['', ' ', '\t', '\n', '  \t  \n  '])
def test_rename_task_with_empty_name_should_fail(service_client: ServiceClient,
                                                 task_factory: Callable[[int], TaskResponse], empty_name: str):
    initial_task = task_factory(1)[0]

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        payload = {'name': empty_name}
        service_client.rename_task(initial_task.id, cast(TaskNameRequest, payload))

    response = exc_info.value.response
    assert response.status_code == 422

    error_detail = response.json()
    assert 'detail' in error_detail
    assert any('Task name must have at least 1 character' in detail.get('msg', '') for detail in error_detail['detail'])

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0


# 1. Создать дефолтный день с 2 задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 2 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствуют текущему дню
# 2. Переименовать одну задачу на имя другой задачи.
#     ОР: Задача не переименована, возвращается ошибка 409 DuplicateTaskNameException: 'Task with name "{task.name}" already exists', обе задачи не изменились, Задач в списке выполненных задач нет
def test_rename_task_to_duplicate_name_should_fail(service_client: ServiceClient,
                                                   task_factory: Callable[[int], List[TaskResponse]]):
    initial_tasks = task_factory(2)
    task_to_rename = initial_tasks[0]
    new_task_name = initial_tasks[1].name

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        request = TaskNameRequest(name=new_task_name)
        service_client.rename_task(task_to_rename.id, request)

    response = exc_info.value.response
    assert response.status_code == 409

    error_response = response.json()
    assert 'error' in error_response
    assert error_response['error'] == f'Task with name "{new_task_name}" already exists'

    final_state = service_client.get_current_state()
    assert len(final_state.current_day_info.tasks) == 2
    assert len(final_state.all_completed_tasks) == 0

    final_active_tasks = final_state.current_day_info.tasks
    assert final_active_tasks == initial_tasks


# 1. Создать дефолтный день с 1 задачей.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 1 задача в текущем дне создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Переименовать задачу на то же самое имя.
#     ОР: Задача осталась с исходным именем, В текущем дне так и осталась 1 задача, остальные параметры не изменились, Задач в списке выполненных задач нет
def test_rename_task_to_same_name(service_client: ServiceClient, task_factory: Callable[[int], List[TaskResponse]]):
    initial_task_list = task_factory(1)
    initial_task = initial_task_list[0]
    new_task_name = initial_task.name

    request = TaskNameRequest(name=new_task_name)
    renamed_task = service_client.rename_task(initial_task.id, request)

    assert_task_data(
        renamed_task,
        expected_id=initial_task.id,
        expected_name=initial_task.name,
        expected_type=initial_task.type,
        expected_status=initial_task.status,
        expected_day_id=initial_task.day_id
    )

    final_state = service_client.get_current_state()
    final_active_task_list = final_state.current_day_info.tasks

    assert len(final_state.current_day_info.tasks) == 1
    assert len(final_state.all_completed_tasks) == 0

    assert final_active_task_list == initial_task_list

