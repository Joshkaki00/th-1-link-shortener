import os

from flask import Flask


def create_app(test_config=None):
    """Application factory — stub until routes/DB are added one def at a time."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "links.sqlite"),
    )
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    return app
