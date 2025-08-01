import pytest
from fastapi.testclient import TestClient
# TODO: переименовать задачу и перелистнуть день? переименовать задачу и установить другой день? (или в другие полноценные кейсы)

# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать 3 задачи. 
#     ОР: 3 задачи созданы с правильными именами, имеют тип 'one-time', статус 'active', day_id соответствует текущему дню
# 3. Переименовать одну задачу.
#     ОР: Задача переименована, остальные ее параметры не поменялись, остальные задачи не изменились

def test_create_and_rename_tasks(client, default_day_state):
    task_names = ['Тестовая задача 1', 'Тестовая задача 2', 'Тестовая задача 3']
    new_task_name = 'Новое имя задачи'

    current_day = default_day_state['current_day_info']

    created_tasks = []
    for task_name in task_names:
        response = client.post('/task/', json={'name': task_name})
        assert response.status_code == 200

        task_data = response.json()
        created_tasks.append(task_data)

        assert task_data['name'] == task_name
        assert task_data['type'] == 'one-time'
        assert task_data['status'] == 'active'
        assert task_data['day_id'] == current_day['id']

    response = client.get('/day/current')
    assert response.status_code == 200
    current_state = response.json()

    current_day_tasks = current_state['current_day_info']['tasks']
    assert len(current_day_tasks) == len(task_names)

    actual_task_names = [task['name'] for task in current_day_tasks]
    assert set(actual_task_names) == set(task_names)

    task_to_rename = created_tasks[1]
    task_to_rename_id = task_to_rename['id']
    response = client.patch(f'/task/{task_to_rename_id}/rename', json={'name': new_task_name})
    assert response.status_code == 200

    renamed_task = response.json()
    assert renamed_task['name'] == new_task_name
    assert renamed_task['id'] == task_to_rename_id
    assert renamed_task['type'] == task_to_rename['type']
    assert renamed_task['status'] == task_to_rename['status']
    assert renamed_task['day_id'] == task_to_rename['day_id']

    response = client.get('/day/current')
    assert response.status_code == 200
    final_state = response.json()

    final_tasks = final_state['current_day_info']['tasks']
    assert len(final_tasks) == len(task_names)
    assert len(final_state['all_completed_tasks']) == 0

    final_task_names = [task['name'] for task in final_tasks]
    assert new_task_name in final_task_names

    renamed_task_in_final = next((task for task in final_tasks if task['id'] == task_to_rename_id), None)
    assert renamed_task_in_final is not None, 'Renamed task changed its id'

    # assert renamed_task_in_final['name'] == new_task_name
    # assert renamed_task_in_final['id'] == task_to_rename_id
    assert renamed_task_in_final['type'] == task_to_rename['type']
    assert renamed_task_in_final['status'] == task_to_rename['status']
    assert renamed_task_in_final['day_id'] == task_to_rename['day_id']

    unchanged_other_tasks_original = [task for task in created_tasks if task['id'] != task_to_rename_id]
    unchanged_other_tasks_final = [task for task in final_tasks if task['id'] != task_to_rename_id]

    assert len(unchanged_other_tasks_original) == len(unchanged_other_tasks_final) == len(task_names) - 1

    unchanged_other_tasks_original.sort(key=lambda x: x['id'])
    unchanged_other_tasks_final.sort(key=lambda x: x['id'])

    for original_task, final_task in zip(unchanged_other_tasks_original, unchanged_other_tasks_final):
        assert original_task == final_task


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


# 1. Получить текущий день.
#     Проверяется фикстурой default_day_state:
#     ОР: День получен, Задач в текущем дне нет, Задач в списке выполненных задач нет
# 2. Создать задачу. Создать задачу только с пробелом
#     ОР: Задача создана с правильным именем, имеет тип 'one-time', статус 'active', day_id соответствует текущему дню.
# 3. Создать задачу с таким же именем.
#     ОР: Задача не создана, возвращается ошибка 409 DuplicateTaskNameException: 'Task with name "{task.name}" already exists'
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
# 2. Поменять имя несуществующей задачи.
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