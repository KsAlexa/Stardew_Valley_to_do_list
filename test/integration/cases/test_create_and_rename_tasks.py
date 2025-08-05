import pytest
from fastapi.testclient import TestClient
from helpers import assert_task_data

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: Получен дефолтный день, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать 3 задачи. 
#     ОР: 3 задачи созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 3. Получить текущий день.
#     ОР: Задач в текущем дне 3, Задач в списке выполненных задач нет
def test_create_tasks(client, default_day_state):
    task_names_list = ['Тестовая задача 1', 'Тестовая задача 2', 'Тестовая задача 3']
    current_day = default_day_state.current_day_info

    created_tasks_from_response = []
    for task_name in task_names_list:
        response = client.post('/task/', json={'name': task_name})
        assert response.status_code == 200

        task_data = response.json()
        created_tasks_from_response.append(task_data)

        assert_task_data(
            task_data,
            expected_name=task_name,
            expected_type='one-time',
            expected_status='active',
            expected_day_id=current_day.id
        )

    response = client.get('/day/current')
    assert response.status_code == 200
    current_state = response.json()

    current_day_tasks_list = current_state['current_day_info']['tasks']
    assert len(current_day_tasks_list) == len(task_names_list)
    assert len(current_state['all_completed_tasks']) == 0

    created_tasks_from_response.sort(key=lambda task: task['id'])
    current_day_tasks_list.sort(key=lambda task: task['id'])
    for created_task, current_day_task in zip(created_tasks_from_response, current_day_tasks_list):
        assert created_task == current_day_task

# 1. Создать дефолтный день с 3мя задачами.
#     Создается и проверяется фикстурой task_factory:
#     ОР: Задач в списке выполненных задач нет, 3 задачи в текущем дне созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 2. Переименовать одну задачу.
#     ОР: Задача переименована, остальные ее параметры не поменялись
# 3. Получить текущий день.
#     ОР: Задач в списке выполненных задач нет, Задач в текущем дне 3, переименованная задача имеет новое имя, остальные задачи не изменились

def test_rename_task(client, task_factory):
    initial_tasks = task_factory(3)
    task_to_rename = initial_tasks[1]
    new_task_name = 'Новое имя 2-й задачи'
    other_initial_tasks = [initial_tasks[0], initial_tasks[2]]

    response = client.patch(f'/task/{task_to_rename.id}/rename', json={'name': new_task_name})
    assert response.status_code == 200
    renamed_task_resp = response.json()

    assert_task_data(
        renamed_task_resp,
        expected_id=task_to_rename.id,
        expected_name=new_task_name,
        expected_type=task_to_rename.type,
        expected_status=task_to_rename.status,
        expected_day_id=task_to_rename.day_id
    )

    response = client.get('/day/current')
    assert response.status_code == 200
    final_state_resp = response.json()
    final_tasks_resp = final_state_resp['current_day_info']['tasks']
    completed_tasks_resp = final_state_resp['all_completed_tasks']

    assert len(final_tasks_resp) == len(initial_tasks)
    assert len(completed_tasks_resp) == 0

    renamed_task_resp = next((task for task in final_tasks_resp if task['id'] == task_to_rename.id), None)
    assert renamed_task_resp is not None
    assert_task_data(
        renamed_task_resp,
        expected_id=task_to_rename.id,
        expected_name=new_task_name,
        expected_type=task_to_rename.type,
        expected_status=task_to_rename.status,
        expected_day_id=task_to_rename.day_id
    )

    other_initial_tasks_dict = [task.model_dump() for task in other_initial_tasks]
    other_final_tasks_resp = [task for task in final_tasks_resp if task['id'] in {task.id for task in other_initial_tasks}]

    other_final_tasks_resp.sort(key=lambda task: task['id'])
    other_initial_tasks_dict.sort(key=lambda task: task['id'])

    assert other_final_tasks_resp == other_initial_tasks_dict

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу с пустым именем. Создать задачу только с пробелом.
#     ОР: Задача не создана, возвращается ошибка 422 ValidationError (или Unprocessable Entity?): 'Task name must have at least 1 character'
@pytest.mark.parametrize('empty_name', ['', ' ', '\t', '\n', '  \t  \n  '])
def test_create_task_with_empty_name_should_fail(client, default_day_state, empty_name):
    current_day = default_day_state['current_day_info']
    
    response = client.post('/task/', json={'name': empty_name})
    assert response.status_code == 422
    
    error_detail = response.json()
    assert 'detail' in error_detail
    assert any('Task name must have at least 1 character' in str(detail) for detail in error_detail['detail'])
    # TODO: проверить, что ничего не создалось


# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу. Создать задачу только с пробелом
#     ОР: Задача создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню.
# 3. Создать задачу с таким же именем.
#     ОР: Задача не создана, возвращается ошибка 409 DuplicateTaskNameException: 'Task with name "{task.name}" already exists'.
def test_create_task_with_duplicate_name_should_fail(client, default_day_state):
    current_day = default_day_state['current_day_info']
    task_name = 'Тестовая задача'
    
    response = client.post('/task/', json={'name': task_name})
    assert response.status_code == 200
    
    task_data = response.json()
    assert task_data['name'] == task_name
    assert task_data['type'] == 'one-time'
    assert task_data['status'] == 'active'
    assert task_data['day_id'] == current_day['id']
    
    response = client.post('/task/', json={'name': task_name})
    assert response.status_code == 409
    
    error_data = response.json()
    assert error_data['error'] == 'Task already exists'



# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу.
#     ОР: Задача создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню.
# 3. Поменять имя несуществующей задачи.
#     ОР: Задача не создана, возвращается ошибка 404 EntityNotFound: 'Task with id "{task.id}" not found', существующая задача не изменилась
def test_rename_nonexistent_task_should_fail(client, default_day_state):
    current_day = default_day_state['current_day_info']
    task_name = 'Тестовая задача'
    new_task_name = 'Новое имя задачи'
    
    response = client.post('/task/', json={'name': task_name})
    assert response.status_code == 200
    
    task_data = response.json()
    existing_task_id = task_data['id']
    assert task_data['name'] == task_name
    assert task_data['type'] == 'one-time'
    assert task_data['status'] == 'active'
    assert task_data['day_id'] == current_day['id']
    
    nonexistent_task_id = existing_task_id + 99
    response = client.patch(f'/task/{nonexistent_task_id}/rename', json={'name': new_task_name})
    assert response.status_code == 404
    
    error_data = response.json()
    assert error_data['error'] == 'Task not found'

    response = client.get('/day/current')
    assert response.status_code == 200
    
    state = response.json()
    tasks = state['current_day_info']['tasks']
    assert len(tasks) == 1
    assert tasks[0]['id'] == task_data['id']
    assert tasks[0]['name'] == task_data['name']
    assert tasks[0]['type'] == task_data['type'] 
    assert tasks[0]['status'] == task_data['status']
    assert tasks[0]['day_id'] == task_data['day_id']


# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу.
#     ОР: Задача создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню.
# 3. Поменять имя задачи на пустую строку. Поменять имя задачи на пробел.
#     ОР: Задача не создана, возвращается ошибка 422 ValidationError (или Unprocessable Entity?): 'Task name must have at least 1 character', существующая задача не изменилась
@pytest.mark.parametrize("empty_name", ['', ' ', '\t', '\n', '  \t  \n  '])
def test_rename_task_with_empty_name_should_fail(client, default_day_state, empty_name):
    current_day = default_day_state['current_day_info']
    task_name = 'Тестовая задача'
    
    response = client.post('/task/', json={'name': task_name})
    assert response.status_code == 200
    
    task_data = response.json()
    task_id = task_data['id']
    assert task_data['name'] == task_name
    assert task_data['type'] == 'one-time'
    assert task_data['status'] == 'active'
    assert task_data['day_id'] == current_day['id']
    
    response = client.patch(f'/task/{task_id}/rename', json={'name': empty_name})
    assert response.status_code == 422
    
    error_detail = response.json()
    assert 'detail' in error_detail
    assert any('Task name must have at least 1 character' in str(detail) for detail in error_detail['detail'])
    
    response = client.get('/day/current')
    assert response.status_code == 200
    
    state = response.json()
    tasks = state['current_day_info']['tasks']
    assert len(tasks) == 1
    assert tasks[0]['id'] == task_data['id']
    assert tasks[0]['name'] == task_data['name']
    assert tasks[0]['type'] == task_data['type']
    assert tasks[0]['status'] == task_data['status']
    assert tasks[0]['day_id'] == task_data['day_id']

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу.
#     ОР: Задача создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню.
# 3. Переименовать задачу на то же самое имя.
#     ОР: Задача переименована, остальные ее параметры не поменялись, остальные задачи не изменились
def test_rename_task_to_same_name(client, default_day_state):
    pass

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать 2 задачи.
#     ОР: Задачи созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствуют текущему дню.
# 3. Переименовать одну задачу на имя другой задачи.
#     ОР: Задача не переименована, возвращается ошибка 409 DuplicateTaskNameException: 'Task with name "{task.name}" already exists', обе задачи не изменились
def test_rename_task_to_duplicate_name_should_fail(): #будет падать, нет обработки на existent name у edit_task
    pass
