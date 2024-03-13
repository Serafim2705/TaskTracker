from flask_httpauth import HTTPTokenAuth
auth = HTTPTokenAuth()
active_tokens = {"test_token": "user11"}