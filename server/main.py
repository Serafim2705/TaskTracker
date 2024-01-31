from flask import Flask, request
from datetime import datetime
from flask import jsonify
from Models import Users as User, Status, Role, TaskBlockTask, SubtaskForTask, Task
from db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPTokenAuth
from flask_cors import CORS
from sqlalchemy import or_
from flask_swagger_ui import get_swaggerui_blueprint
import yaml
import json

app = Flask(__name__)
CORS(app)
auth = HTTPTokenAuth()
app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

active_tokens = {"test_token": "user11"}


@app.route('/swagger.json')
def swagger_file():
    with open('spec-open-api.yml', 'r', encoding='utf-8') as file:
        spec = yaml.safe_load(file)
    json_spec = json.dumps(spec)
    return json_spec


SWAGGER_URL = '/swagger'
app.register_blueprint(get_swaggerui_blueprint(
    SWAGGER_URL,
    '/swagger.json',
    config={
        'app_name': "My Flask API"
    }
))


@auth.verify_token
def verify_token(token):
    user = active_tokens.get(token)
    if not user:
        return False
    return user


@app.route('/user/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return {"Message": 'Неверный формат запроса'}, 400

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.user_password, password):
            return {"Message": 'Неверный логин или пароль'}, 401

        for token, name in active_tokens.items():
            if name == username:
                active_tokens.pop(token)
                break

        token = generate_password_hash(username)
        active_tokens[token] = username
        user_role = None
        if user.role_name:
            user_role = user.role_name.name

        response = jsonify(
            {'message': 'Авторизация выполнена успешно!', "Authorization": token, "code": 200, "user": username,
             "role": user_role})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200


@app.route('/user/logout', methods=['POST'])
@auth.login_required
def logout():
    token = request.headers.get('Authorization')
    if not token:
        return {"Message": "Несуществующий токен"}, 403
    token = token[7:]
    active_tokens.pop(token)
    return {"Message": 'Logout success', "code": 200}, 200


@app.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    # TODO роль выбирать самому нельзя??
    if not username or not password:
        return {"Message": 'Неверный формат запроса'}, 400

    user = User.query.filter_by(username=username).first()
    if user:
        return {"Message": 'Пользователь с таким именем уже существует'}, 400
    try:
        new_user = User(username=username, user_password=generate_password_hash(password), role_name=role)
        db.session.add(new_user)
        db.session.commit()
    except:
        return {"Message": 'Неизвестная ошибка'}, 500
    token = generate_password_hash(username)
    active_tokens[token] = username
    return {"Message": 'Регистрация выполнена успешно!',
            "Authorization": token}, 200


@app.route('/user/change_password', methods=['POST'])
@auth.login_required
def change_passwords():
    data = request.get_json()
    new_password = data.get('new_password')
    prev_password = data.get('prev_password')
    if not prev_password or not new_password:
        return {"Message": 'Неверный формат запроса'}, 400

    try:
        user = User.query.filter_by(username=auth.current_user()).first()
    except:
        return {"Message": 'Неизвестная ошибка сервера, пользователь не найден в базе'}, 500

    if not user or not check_password_hash(user.user_password, prev_password):
        return {"Message": 'Неверный пароль'}, 403
    user.user_password = generate_password_hash(new_password)

    try:
        db.session.add(user)
        db.session.commit()
    except:
        return {"Message": 'Неизвестная ошибка'}, 500

    token = request.headers.get('Authorization')
    token = token[7:]
    active_tokens.pop(token)
    token = generate_password_hash(auth.current_user())
    active_tokens[token] = auth.current_user()
    return {"Message": 'Пароль успешно изменен',
            "Authorization": token}, 200


@app.route('/user/change_user', methods=['POST'])
@auth.login_required
def change_user():
    cur_user = User.query.filter_by(username=auth.current_user()).first()
    if cur_user.role_name:
        if cur_user.role_name.name != "Manager":
            return {"Message": 'Только менеджер может изменять данные других пользователей '}, 403
    else:
        return {"Message": 'Только менеджер может изменять данные других пользователей '}, 403
    data = request.get_json()
    prev_username = data.get('prev_username')
    user_id = data.get('user_id')
    new_role = data.get('new_role')
    new_username = data.get('new_username')
    if prev_username:
        cur_user = User.query.filter_by(username=prev_username).first()
    elif user_id:
        cur_user = User.query.filter_by(id=user_id).first()
    else:
        return {"Message": 'Неверный формат, требуется id или username пользователя!'}, 400
    if not cur_user:
        return {"Message": 'Пользователь с такими данными не найден!'}, 404

    if not new_role and not new_username:
        return {"Message": 'Укажите новый логин или роль'}, 400

    if new_role:
        if new_role not in [e.name for e in Role]:
            return {"Message": 'Неверная роль!'}, 404
        cur_user.role_name = new_role

    if new_username:
        if User.query.filter_by(username=new_username).first():
            return {"Message": 'Имя занято!'}, 400
        cur_user.username = new_username
        for token, user in active_tokens:
            if user == auth.current_user():
                active_tokens[token] = new_username
                break

    db.session.add(cur_user)
    db.session.commit()

    return {"Message": 'Данные успешно обновлены!'}, 200


@app.route('/task/create', methods=['POST'])
@auth.login_required
def create_task():
    data = request.get_json()
    type_of_task = data.get('type_of_task')
    priority = data.get('priority')
    topic = data.get('topic')
    if Task.query.filter_by(topic=topic).first():
        return {"Message": 'Задача с таким названием уже существует '}, 400
    description = data.get('description')
    executor = data.get('executor')
    date_of_edit = date_of_found = datetime.now()
    if type_of_task not in [0, 1] or priority not in range(1, 5) or (executor and type(executor) != int):
        return {"Message": 'Неверный формат запроса'}, 400

    sub_tasks = data.get('sub_tasks')
    prev_tasks = data.get('prev_tasks')

    if sub_tasks or prev_tasks:
        all_tasks = Task.query.group_by(Task.id).all()
        all_tasks_ids = [e.id for e in all_tasks]

        if sub_tasks and (set(sub_tasks) - set(all_tasks_ids)):
            return {"Message": 'Неверные подзадачи'}, 400

        if prev_tasks and (set(prev_tasks) - set(all_tasks_ids)):
            return {"Message": 'Неверные блокирующие задачи'}, 400

    cur_user = User.query.filter_by(username=auth.current_user()).first()
    if cur_user:
        if not cur_user.role_name:
            return {"Message": 'Только пользователь с правами менеджера может создавать задачи'}, 403
        if cur_user.role_name.name != 'Manager':
            return {"Message": 'Только пользователь с правами менеджера может создавать задачи'}, 403
    else:
        return {"Message": 'Внутрення ошибка сервера'}, 500

    if executor:
        user = User.query.filter_by(id=executor).first()
        if not user:
            return {"Message": 'Неверный исполнитель'}, 404
        if not user.role_name:
            return {"Message": 'Исполнителю не назначена роль'}, 400
        if user.role_name.name == 'Manager':
            return {"Message": 'Менеджер не может быть исполнителем задачи!'}, 400

    new_task = Task(type_of_task=type_of_task, topic=topic, description=description,
                    priority=priority, status='To_do', executor=executor,
                    date_of_found=date_of_found, date_of_edit=date_of_edit, owner_task=cur_user.id)

    db.session.add(new_task)
    db.session.flush()

    if sub_tasks:
        sub_tasks = list(set(sub_tasks))

        #  подзадача мб привязана только к любой другой (основной задаче), которая не имеет "надзадач"
        incorrect_id = check_subtasks(sub_tasks, new_task.id)
        if incorrect_id:
            db.session.rollback()
            return {"Message": f'task {incorrect_id} already have subtask or is a subtask itself'}, 404
        try:
            for id_sub in sub_tasks:
                db.session.add(SubtaskForTask(main_id=new_task.id, subtask_id=id_sub))
            db.session.commit()
        except:
            db.session.rollback()
            return {"Message": 'error of writing'}, 500

    #  блокированная задача не может быть дальше блокируемая ( кроме want fix)
    #   для каждой из блокируемых (левых) смотрим следующую , идем до конца, или пока не встретим начало

    if prev_tasks:
        prev_tasks = list(set(prev_tasks))
        for id_prev in prev_tasks:
            tb = Task.query.filter_by(id=id_prev).first()

            if tb.status.name not in ['To_do', 'Wont_fix']:
                return {
                           "Message": F'задача {tb.topic} не может блокировать задачу {topic}, т.к. находится на '
                                      F'этапе выше'}, 400

            db.session.add(TaskBlockTask(blocked_id=new_task.id, block_id=id_prev))
    db.session.commit()

    return {"Message": 'Задача создана!'}, 200


@app.route('/task/blocked_task', methods=['PUT'])
@auth.login_required
def edit_blocked_task():
    data = request.get_json()

    main_task_id = data.get('main_task_id')
    block_tasks = data.get('block_tasks')

    if not block_tasks or not main_task_id:
        return {"Message": 'Неверные параметры запроса'}, 400
    block_tasks = list(set(block_tasks))
    all_tasks = Task.query.all()
    tasks_ids = [e.id for e in all_tasks]

    if main_task_id not in tasks_ids:
        return {"Message": 'Неверный id'}, 404
    dic_t = dict()

    for task in all_tasks:
        dic_t[task.id] = task.status.name

    for task in block_tasks:
        if task == main_task_id:
            return {"Message": 'Несуществующие задачи в block_tasks'}, 404
        if task not in tasks_ids:
            return {"Message": f'Задача и id {task} не существует'}, 404
        status_l = [e.name for e in Status]
        if status_l.index(dic_t[task]) < status_l.index(dic_t[main_task_id]) and not (
                dic_t[task] == 'Wont_fix' or dic_t[main_task_id] == 'Wont_fix'):
            return {
                       "Message": f'Задача из {dic_t[main_task_id]} не может быть заблокирована задачей из {dic_t[task]}'}, 403

    prev_block_tasks = TaskBlockTask.query.filter_by(blocked_id=main_task_id).all()

    for prev_block_task in prev_block_tasks:
        db.session.delete(prev_block_task)

    for id_block_task in block_tasks:
        db.session.add(TaskBlockTask(blocked_id=main_task_id, block_id=id_block_task))
    db.session.commit()
    # todo рекурсивный обход в глубину, чтобы исключить цикл блокировок

    return {"Message": f'блокируемые задачи для задачи с id={main_task_id} обновлены'}, 200


def check_subtasks(sub_tasks, new_task_id):
    all_sub_tasks_ids = set()
    all_sub_tasks = SubtaskForTask.query.all()
    for task in all_sub_tasks:
        all_sub_tasks_ids.add(task.main_id)
        all_sub_tasks_ids.add(task.subtask_id)
    #  подзадача мб привязана только к любой другой (основной задаче), которая не имеет "надзадач"
    for id_sub in sub_tasks:
        if id_sub in all_sub_tasks_ids or id_sub == new_task_id:
            return id_sub
        if new_task_id in all_sub_tasks_ids:
            return new_task_id
    return False


@app.route('/task/subtasks', methods=['PUT'])
@auth.login_required
def edit_subtasks_task():
    data = request.get_json()
    main_task_id = data.get('main_task_id')
    subtasks = data.get('subtasks')

    if not main_task_id:
        return {"Message": 'Неверный id'}, 400
    if not subtasks:
        return {"Message": 'Неверные параметры запроса'}, 400
    subtasks = list(set(subtasks))
    all_tasks = Task.query.all()
    tasks_ids = [e.id for e in all_tasks]
    for task in subtasks:
        if task == main_task_id:
            return {"Message": 'Некорректная подзадача'}, 400
        if task not in tasks_ids:
            return {"Message": f'Задача с индексом {task} не существует'}, 404

    incorrect_id = check_subtasks(subtasks, main_task_id)
    if incorrect_id:
        return {"Message": f'Задача с индексом {incorrect_id} уже имеет подзадачу или сама является подзадачей'}, 400

    prev_subtasks = SubtaskForTask.query.filter_by(main_id=main_task_id).all()

    for prev_subtask in prev_subtasks:
        db.session.delete(prev_subtask)

    for id_sub in subtasks:
        db.session.add(SubtaskForTask(main_id=main_task_id, subtask_id=id_sub))
    db.session.commit()
    return {"Message": 'Подзадачи обновлены'}, 200


@app.route('/task/executor', methods=['PUT'])
@auth.login_required
def edit_executor_task():
    data = request.get_json()
    task_id = data.get('task_id')
    new_executor_id = data.get('new_executor_id')
    changing_task = Task.query.filter_by(id=task_id).first()
    if not task_id or (not new_executor_id and new_executor_id != 0):
        return {'Message': "Неверный запрос"}, 400
    if not changing_task:
        return {'Message': "Задача с таким id не существует"}, 404
    if changing_task.status.name == 'In_progress' and new_executor_id == 0:
        return {'Message': "Нельзя снимать исполнителя с задачи in progress"}, 400
    if new_executor_id == 0:
        changing_task.executor = None
        db.session.add(changing_task)
        db.session.commit()
        return {'Message': "Исполнитель снят"}, 200

    executor = User.query.filter_by(id=new_executor_id).first()
    if not executor:
        return {'Message': "Исполнитель с таким id не существует"}, 404

    if not executor.role_name:
        return {'Message': "Исполнителю не назначена роль"}, 400
    if executor.role_name.name == 'Manager':
        return {'Message': "Manager не может быть исполнителем"}, 400

    if changing_task.status.name in ['In_progress', 'Code_review', 'Dev_test'] and executor.role_name.name == 'Tester':
        return {'Message': "Tester не может быть исполнителем для этой задачи"}, 400

    if changing_task.status.name == 'Testing' and executor.role_name.name == 'Developer':
        return {'Message': "Developer не может быть исполнителем для этой задачи"}, 400

    changing_task.executor = new_executor_id
    changing_task.date_of_edit = datetime.now()
    db.session.add(changing_task)
    db.session.commit()
    return {'Message': "Исполнитель успешно обновлен"}, 200


@app.route('/task/info', methods=['PUT'])
@auth.login_required
def edit_info_task():
    data = request.get_json()
    task_id = data.get('task_id')
    new_priority = data.get('new_priority')
    description = data.get('description')
    title = data.get('title')
    type_task = data.get('type')

    if not task_id:
        return {'Message': 'Отсутствует id задачи'}, 400

    if not new_priority and not description and not title and type_task is None:
        return {'Message': 'Пропущены обязательные параметры'}, 400

    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return {'Message': 'Задача с заданным id не найдена'}, 404
    if new_priority:
        if new_priority not in range(1, 5):
            return {'Message': 'Неверный приоритет задачи: укажите число от 1 до 5'}, 400
        task.priority = new_priority
    if description:
        task.description = description

    if title:
        if Task.query.filter_by(topic=title).first():
            return {'Message': 'Выбранная тема задачи уже занята'}, 400
        task.topic = title
    if type_task:
        if type_task not in [0, 1]:
            return {'Message': 'Неверный тип задачи: укажите 1 для task, 0 для bug'}, 400
        task.type_of_task = type_task
    if description:
        task.description = description
    task.date_of_edit = datetime.now()
    db.session.add(task)
    db.session.commit()

    return {'Message': 'Задача обновлена успешно!'}, 200


@app.route('/task/status', methods=['PUT'])
@auth.login_required
def edit_status_task():
    data = request.get_json()
    task_id = data.get('task_id')
    new_status = data.get('new_status')
    if not task_id or not new_status:
        return {'Message': "Неверный запрос"}, 400
    changing_task = Task.query.filter_by(id=task_id).first()
    if not changing_task:
        return {'Message': "Задача с таким id не существует"}, 404

    if new_status == 'In_progress' and not changing_task.executor:
        return {'Message': "Требуется исполнитель"}, 400
    executor = None
    if changing_task.executor:
        executor = User.query.filter_by(id=changing_task.executor).first()

    if new_status in ['In_progress', 'Code_review', 'Dev_test'] and executor:
        if executor.role_name:
            if executor.role_name.name == 'Tester':
                return {'Message': "Тестировщик не может быть назначен на эту задачу"}, 400
        else:
            return {'Message': "У исполнителя не определена роль"}, 400

    if new_status == "Testing" and executor:
        if executor.role_name:
            if executor.role_name.name == 'Developer':
                return {'Message': "Developer не может быть назначен на эту задачу"}, 400
        else:
            return {'Message': "У исполнителя не определена роль"}, 400

    if new_status not in [e.name for e in Status]:
        return {'Message': "Несуществующий статус"}, 404

    if new_status not in ['To_do', 'Wont_fix']:
        if [e.name for e in Status].index(new_status) != (
                [e1.name for e1 in Status].index(changing_task.status.name) + 1):
            return {'Message': "Невозможно изменить статус на указанный"}, 400
        status_l = [e.name for e in Status]

        block_tasks = TaskBlockTask.query.filter_by(blocked_id=task_id).all()
        for bt in block_tasks:
            block_task = Task.query.filter_by(id=bt.block_id).first()
            if status_l.index(block_task.status.name) < status_l.index(new_status) and not (
                    new_status == 'Wont_fix' or block_task.status.name == 'Wont_fix'):
                return {
                           'Message': f'задача {block_task.topic} из {block_task.status.name} '
                                      f'не позволяет задаче {changing_task.topic} перейти в статус {new_status} '}, 400

    changing_task.status = new_status
    changing_task.date_of_edit = datetime.now()
    db.session.add(changing_task)
    db.session.commit()
    return {'Message': "Статус изменен", 'code': 200}, 200


@app.route('/task/', methods=['GET'])
@auth.login_required
def get_tasks():
    text = request.args.get('text')
    response = {}
    if text:
        task_list = Task.query.filter(
            or_(Task.topic.ilike(f'%{text.lower()}%'), Task.description.ilike(f'%{text.lower()}%'))).order_by(
            Task.date_of_edit.desc()).all()
    else:
        task_list = Task.query.order_by(Task.date_of_edit.desc()).all()

    users_dict = {}
    users = User.query.all()
    for user in users:
        users_dict[user.id] = [user.id, user.username, user.role_name.name]
    subtasks = SubtaskForTask.query.all()
    blocktasks = TaskBlockTask.query.all()
    for task in task_list:
        tasks_for_status = response.get(task.status.name)
        next_task = {"title": task.topic, "description": task.description,
                     "id": task.id, "executor": users_dict.get(task.executor), "edit_date": task.date_of_edit,
                     "create_date": task.date_of_found, "priority": task.priority,
                     "type_id": task.type_of_task, "creator": users_dict.get(task.owner_task),
                     "subtasks": [[e.subtask_id] for e in subtasks if e.main_id == task.id],
                     "blocked_tasks": [[e.blocked_id] for e in blocktasks if e.block_id == task.id],
                     "block_tasks": [[e.block_id] for e in blocktasks if e.blocked_id == task.id]}
        if tasks_for_status:
            tasks_for_status.append(next_task)
            response[task.status.name] = tasks_for_status
        else:
            response[task.status.name] = [next_task]

    task_dict = {}
    all_tasks = Task.query.all()

    for task in all_tasks:
        task_dict[task.id] = [task.id, task.topic, task.executor, task.description,
                              task.type_of_task, task.priority, task.status.name,
                              task.date_of_edit, task.date_of_found, task.owner_task]

    for status, _tasks in response.items():
        for _task_n in range(len(_tasks)):

            sts = response[status][_task_n]['subtasks']
            if sts:
                for i in range(len(sts)):
                    _id = response[status][_task_n]['subtasks'][i][0]
                    response[status][_task_n]['subtasks'][i] = task_dict[_id]
                    response[status][_task_n]['subtasks'][i][9] = users_dict.get(
                        response[status][_task_n]['subtasks'][i][9])
                    response[status][_task_n]['subtasks'][i][2] = users_dict.get(
                        response[status][_task_n]['subtasks'][i][2])
            bts = response[status][_task_n]['blocked_tasks']
            if bts:
                for i in range(len(bts)):
                    _id = response[status][_task_n]['blocked_tasks'][i][0]
                    response[status][_task_n]['blocked_tasks'][i] = task_dict[_id]
                    response[status][_task_n]['blocked_tasks'][i][9] = users_dict.get(
                        response[status][_task_n]['blocked_tasks'][i][9])
                    response[status][_task_n]['blocked_tasks'][i][2] = users_dict.get(
                        response[status][_task_n]['blocked_tasks'][i][2])

            bts2 = response[status][_task_n]['block_tasks']
            if bts2:
                for i in range(len(bts2)):
                    _id = response[status][_task_n]['block_tasks'][i][0]
                    response[status][_task_n]['block_tasks'][i] = task_dict[_id]
                    response[status][_task_n]['block_tasks'][i][9] = users_dict.get(
                        response[status][_task_n]['block_tasks'][i][9])
                    response[status][_task_n]['block_tasks'][i][2] = users_dict.get(
                        response[status][_task_n]['block_tasks'][i][2])

    response['code'] = 200
    response = jsonify(response)

    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200


@app.route('/task/<int:task_id>', methods=['GET'])
@auth.login_required
def get_task_id(task_id):
    if not task_id:
        return {'Message': 'не указан id'}, 400
    task = Task.query.filter_by(id=task_id).first()

    if not task:
        return {'Message': f'задача с id={task_id} не найдена'}, 404
    users = User.query.all()
    users_dict = {}
    for user in users:
        users_dict[user.id] = user.username
    blocked_tasks = TaskBlockTask.query.filter_by(block_id=task_id).all()
    blocked_tasks_list = []
    for e in blocked_tasks:
        t = Task.query.filter_by(id=e.blocked_id).first()
        blocked_tasks_list.append({"title": t.topic, "description": t.description, "status": t.status.name,
                                   "id": t.id, "executor": users_dict[t.executor], "edit_date": t.date_of_edit,
                                   "create_date": t.date_of_found, "priority": t.priority,
                                   "type_id": t.type_of_task, "creator": users_dict[t.owner_task]})

    block_tasks = TaskBlockTask.query.filter_by(blocked_id=task_id).all()
    block_tasks_list = []
    for e in block_tasks:
        t = Task.query.filter_by(id=e.block_id).first()
        block_tasks_list.append({"title": t.topic, "description": t.description, "status": t.status.name,
                                 "id": t.id, "executor": users_dict[t.executor], "edit_date": t.date_of_edit,
                                 "create_date": t.date_of_found, "priority": t.priority,
                                 "type_id": t.type_of_task, "creator": users_dict[t.owner_task]})

    subtasks = SubtaskForTask.query.filter_by(main_id=task_id).all()
    subtasks_list = []
    for e in subtasks:
        t = Task.query.filter_by(id=e.main_id).first()
        subtasks_list.append({"title": t.topic, "description": t.description, "status": t.status.name,
                              "id": t.id, "executor": users_dict[t.executor], "edit_date": t.date_of_edit,
                              "create_date": t.date_of_found, "priority": t.priority,
                              "type_id": t.type_of_task, "creator": users_dict[t.owner_task]})

    response = {"title": task.topic, "description": task.description, "status": task.status.name,
                "id": task.id, "executor": users_dict.get(task.executor), "edit_date": task.date_of_edit,
                "create_date": task.date_of_found, "priority": task.priority,
                "type_id": task.type_of_task, "creator": users_dict[task.owner_task],
                "subtasks": subtasks_list,
                "blocked_tasks": blocked_tasks_list,
                "block_tasks": block_tasks_list}
    return response, 200


@app.route('/task/delete/<int:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    if not task_id:
        return {'Message': "Неверный запрос"}, 400
    cur_user = User.query.filter_by(username=auth.current_user()).first()
    if not cur_user:
        return {'Message': "Внутрення ошибка при проверке токена"}, 500
    if not cur_user.role_name:
        return {'Message': "Только менеджер может удалять задачу"}, 403
    if cur_user.role_name.name != 'Manager':
        return {'Message': "Только менеджер может удалять задачу"}, 403

    del_task = Task.query.filter_by(id=task_id).first()
    if not del_task:
        return {'Message': "Задача с таким id не найдена"}, 404
    db.session.delete(del_task)

    subs_del = SubtaskForTask.query.filter(
        or_(SubtaskForTask.subtask_id == task_id, SubtaskForTask.main_id == task_id)).all()
    for sub_del in subs_del:
        db.session.delete(sub_del)

    blocks_del = TaskBlockTask.query.filter(
        or_(TaskBlockTask.blocked_id == task_id, TaskBlockTask.block_id == task_id)).all()
    for block_del in blocks_del:
        db.session.delete(block_del)

    try:
        db.session.commit()
    except:
        return {'Message': "Неизвестная ошибка сервера"}, 500
    return {'Message': "Задача удалена успешно!"}, 200


if __name__ == "__main__":
    app.run(debug=True)
    db.create_all()
