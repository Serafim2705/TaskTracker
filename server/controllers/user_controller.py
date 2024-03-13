from flask import Flask, request
from flask import jsonify
from server.Models import Users as User, Status, Role
from werkzeug.security import generate_password_hash, check_password_hash
import re
from server.init_app import auth,active_tokens,db,app
from flask import Blueprint

user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/user/login', methods=['POST'])
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


@user_bp.route('/user/logout', methods=['POST'])
@auth.login_required
def logout():
    token = request.headers.get('Authorization')
    if not token:
        return {"Message": "Несуществующий токен"}, 403
    token = token[7:]
    active_tokens.pop(token)
    return {"Message": 'Logout success', "code": 200}, 200


@user_bp.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    pattern = r'^[a-zA-Z0-9]+$'

    if not username or not password:
        return {"Message": 'Неверный формат запроса'}, 400

    if not re.match(pattern, username):
        return {"Message": 'Логин должен содержать только латинские символы и цифры'}, 400
    if len(str(username)) < 5 or len(str(username)) > 10:
        return {"Message": 'Логин должен быть от 5 до 10 символов'}, 400

    if not re.match(pattern, password):
        return {"Message": 'Пароль должен содержать только латинские символы и цифры'}, 400
    if len(str(password)) < 5 or len(str(password)) > 15:
        return {"Message": 'Пароль должен быть от 5 до 15 символов'}, 400

    user = User.query.filter_by(username=username).first()

    if user:
        return {"Message": 'Пользователь с таким именем уже существует'}, 400

    new_user = User(username=username, user_password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    token = generate_password_hash(username)
    active_tokens[token] = username
    return {"Message": 'Регистрация выполнена успешно!',
            "Authorization": token}, 200


@user_bp.route('/user/change_password', methods=['POST'])
@auth.login_required
def change_passwords():
    data = request.get_json()
    new_password = data.get('new_password')
    prev_password = data.get('prev_password')
    pattern = r'^[a-zA-Z0-9]+$'
    if not prev_password or not new_password:
        return {"Message": 'Неверный формат запроса'}, 400

    if not re.match(pattern, new_password):
        return {"Message": 'Пароль должен содержать только латинские символы и цифры'}, 400
    if len(str(new_password)) < 5 or len(str(new_password)) > 15:
        return {"Message": 'Пароль должен быть от 5 до 15 символов'}, 400

    try:
        user = User.query.filter_by(username=auth.current_user()).first()
    except:
        return {"Message": 'Неизвестная ошибка сервера, пользователь не найден в базе'}, 500

    if not user or not check_password_hash(user.user_password, prev_password):
        return {"Message": 'Неверный пароль'}, 403
    user.user_password = generate_password_hash(new_password)

    # db.session.merge(user)
    cur_session = db.session.object_session(user)
    cur_session.commit()

    token = request.headers.get('Authorization')
    token = token[7:]
    active_tokens.pop(token)
    token = generate_password_hash(auth.current_user())
    active_tokens[token] = auth.current_user()
    return {"Message": 'Пароль успешно изменен',
            "Authorization": token}, 200


@user_bp.route('/user/change_user', methods=['POST'])
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
        new_user = User.query.filter_by(username=prev_username).first()
    elif user_id:
        new_user = User.query.filter_by(id=user_id).first()
    else:
        return {"Message": 'Неверный формат, требуется id или username пользователя!'}, 400
    if not new_user:
        return {"Message": 'Пользователь с такими данными не найден!'}, 404

    if not new_role and not new_username:
        return {"Message": 'Укажите новый логин или роль'}, 400

    if new_role:
        if new_role not in [str(e.name) for e in Role]:
            return {"Message": 'Неверная роль!'}, 404
        new_user.role_name = new_role

    pattern = r'^[a-zA-Z0-9]+$'
    if new_username:
        if not re.match(pattern, new_username):
            return {"Message": 'Логин должен содержать только латинские символы и цифры'}, 400
        if len(str(new_username)) < 5 or len(str(new_username)) > 10:
            return {"Message": 'Логин должен быть от 5 до 10 символов'}, 400

        if User.query.filter_by(username=new_username).first():
            return {"Message": 'Имя занято!'}, 400
        new_user.username = new_username
        for token, user in active_tokens.items():
            if user == prev_username:
                active_tokens[token] = new_username
                break

    cur_session = db.session.object_session(new_user)
    cur_session.add(new_user)

    cur_session.commit()

    return {"Message": 'Данные успешно обновлены!'}, 200
