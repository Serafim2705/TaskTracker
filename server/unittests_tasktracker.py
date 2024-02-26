import unittest
import json
from main import app
# from init_app import *
from db import db
from Models import Users as User, Status, Role, TaskBlockTask, SubtaskForTask, Task
from datetime import datetime


class APITestCase(unittest.TestCase):
    token = ''

    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/test_db'

        db.init_app(app)
        with app.app_context():
            print('Создаем таблицы для теста')
            db.create_all()
            nu = User(username='user',
                      user_password='pbkdf2:sha256:260000$BepKulhoi1rBbF3R$42264357a0dd65a0c0e6a93f8cc191a4faad8182913e50600286a7b681860561',
                      role_name='Team_lead')
            db.session.add(nu)
            nu = User(username='user2',
                      user_password='pbkdf2:sha256:260000$BepKulhoi1rBbF3R$42264357a0dd65a0c0e6a93f8cc191a4faad8182913e50600286a7b681860561',
                      role_name='Manager')
            db.session.add(nu)
            nu = User(username='user3',
                      user_password='pbkdf2:sha256:260000$BepKulhoi1rBbF3R$42264357a0dd65a0c0e6a93f8cc191a4faad8182913e50600286a7b681860561',
                      role_name='Tester')
            db.session.add(nu)
            db.session.commit()
            nt = Task(type_of_task=1, priority=1, status='To_do', topic='Test', description='test', executor=1,
                      owner_task=1, date_of_edit=datetime.now(), date_of_found=datetime.now())
            db.session.add(nt)
            nt = Task(type_of_task=1, priority=1, status='To_do', topic='Test2', description='test', executor=1,
                      owner_task=1, date_of_edit=datetime.now(), date_of_found=datetime.now())
            db.session.add(nt)
            nt = Task(type_of_task=1, priority=1, status='To_do', topic='Test3', description='test', executor=1,
                      owner_task=1, date_of_edit=datetime.now(), date_of_found=datetime.now())
            db.session.add(nt)
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            print('Удаляем таблицы для теста')
            db.session.rollback()
            db.drop_all()

    def test_1_post_login(self):
        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000'}

        params = {'username': 'user', 'password': 'not_test'}
        response = self.app.post('/user/login', json=params, headers=headers1)
        self.assertEqual(response.status_code, 401)

        params = {'username': 'user'}
        response = self.app.post('/user/login', json=params, headers=headers1)
        self.assertEqual(response.status_code, 400)

        params = {'username': 'user2', 'password': 'test'}
        response = self.app.post('/user/login', json=params, headers=headers1)
        response_body_str = response.data.decode('utf-8')
        response_body_json = json.loads(response_body_str)
        self.__class__.token = response_body_json.get('Authorization')  # Присваиваем значение token
        self.assertEqual(response.status_code, 200)

    def test_post_task(self):
        # print('ТОКЕН:', self.__class__.token)
        params = {"Content-Type": "application/json",
                  "Host": "127.0.0.1",
                  "type_of_task": 1,
                  "sub_tasks": [
                  ],
                  "prev_tasks": [
                  ],
                  "priority": 1,
                  "executor": 1,
                  "description": "test_task",
                  "topic": "test1112"
                  }
        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + self.__class__.token}
        response = self.app.post('/task/create', json=params, headers=headers1)
        self.assertEqual(response.status_code, 200)

        response = self.app.post('/task/create', json=params, headers=headers1)
        self.assertEqual(response.status_code, 400)

        params = {"Content-Type": "application/json",
                  "Host": "127.0.0.1",
                  "type_of_task": 0,
                  "sub_tasks": [
                  ],
                  "prev_tasks": [
                  ],
                  "priority": 1,
                  "executor": 11,
                  "description": "test_task",
                  "topic": "test1"
                  }
        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + self.__class__.token}
        response = self.app.post('/task/create', json=params, headers=headers1)
        self.assertEqual(response.status_code, 404)

    def test_get_tasks(self):
        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + self.__class__.token}
        response = self.app.get('/task/', headers=headers1)

        response_body_str = response.data.decode('utf-8')
        response_body_json = json.loads(response_body_str)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_body_json['To_do'])
        response = self.app.get('/task/1', headers=headers1)
        response_body_str = response.data.decode('utf-8')
        response_body_json = json.loads(response_body_str)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_body_json['edit_date'])

        params = {'text': 'test'}
        response = self.app.get('/task/', query_string=params, headers=headers1)
        self.assertEqual(response.status_code, 200)
        response_body_str = response.data.decode('utf-8')
        response_body_json = json.loads(response_body_str)
        self.assertTrue(response_body_json.get('To_do'))


    def test_post_logout(self):

        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + 'test_token'}
        response = self.app.post('/user/logout', headers=headers1)
        self.assertEqual(response.status_code, 200)

        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + 'test_token'}
        response = self.app.post('/user/logout', headers=headers1)
        self.assertEqual(response.status_code, 401)

        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000'}
        response = self.app.post('/user/logout', headers=headers1)
        self.assertEqual(response.status_code, 401)

    def test_edit_task_status(self):
        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + self.__class__.token}
        params = {'task_id': 1, 'new_status': 'In_progress'}
        response = self.app.put('/task/status', headers=headers1, json=params)
        self.assertEqual(response.status_code, 200)

        params = {'task_id': 2, 'new_status': 'Done'}
        response = self.app.put('/task/status', headers=headers1, json=params)
        self.assertEqual(response.status_code, 400)

        params = {'task_id': 2, 'new_status': 'incorrect_status'}
        response = self.app.put('/task/status', headers=headers1, json=params)
        self.assertEqual(response.status_code, 404)

        params = {'task_id': 12, 'new_status': 'Done'}
        response = self.app.put('/task/status', headers=headers1, json=params)
        self.assertEqual(response.status_code, 404)

        params = {'new_status': 'Done'}
        response = self.app.put('/task/status', headers=headers1, json=params)
        self.assertEqual(response.status_code, 400)

    def test_edit_task_executor(self):
        headers1 = {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'Access-Control-Allow-Origin': 'http://127.0.0.1:5000',
                    'Authorization': 'Bearer ' + self.__class__.token}
        params = {'task_id': 2, 'new_executor_id': 2}
        response = self.app.put('/task/executor', headers=headers1, json=params)
        self.assertEqual(response.status_code, 400)

        params = {'task_id': 2}
        response = self.app.put('/task/executor', headers=headers1, json=params)
        self.assertEqual(response.status_code, 400)

        params = {'task_id': 122, 'new_executor_id': 3}
        response = self.app.put('/task/executor', headers=headers1, json=params)
        self.assertEqual(response.status_code, 404)

        params = {'task_id': 2, 'new_executor_id': 3}
        response = self.app.put('/task/executor', headers=headers1, json=params)
        self.assertEqual(response.status_code, 200)

        params = {'task_id': 2, 'new_executor_id': 0}
        response = self.app.put('/task/executor', headers=headers1, json=params)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
