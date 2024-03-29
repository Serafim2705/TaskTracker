from flask_swagger_ui import get_swaggerui_blueprint
import yaml
import json
from server.init_app import auth, active_tokens,app

with app.app_context():
    from controllers.user_controller import user_bp

    app.register_blueprint(user_bp)
    from controllers.task_controller import task_bp

    app.register_blueprint(task_bp)


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


if __name__ == "__main__":
    app.run(debug=True)
