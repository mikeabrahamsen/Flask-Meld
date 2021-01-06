import os
from flask import send_from_directory
from flask_socketio import SocketIO
from .tag import MeldTag, MeldScriptsTag
from .message import process_message


class Meld:
    def __init__(self, app=None, socketio=None, **kwargs):
        self.app = app

        if app is not None:
            self.init_app(app, socketio=socketio, **kwargs)

    def send_static_file(self, filename):
        """Send a static file from the flask-meld static directory."""
        _static_dir = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "static/js")
        )
        return send_from_directory(_static_dir, filename)

    def init_app(self, app, socketio=None, **kwargs):
        app.jinja_env.add_extension(MeldTag)
        app.jinja_env.add_extension(MeldScriptsTag)
        if socketio:
            app.socketio = socketio
        else:
            app.socketio = SocketIO(app, **kwargs)

        meld_dir = app.config.get("MELD_COMPONENT_DIR", None)
        if meld_dir:
            if not os.path.isabs(meld_dir):
                directory = os.path.abspath(os.path.join(app.root_path, meld_dir))
                app.config["MELD_COMPONENT_DIR"] = directory

        if not app.config.get("SECRET_KEY"):
            raise RuntimeError(
                "The Flask-Meld requires the 'SECRET_KEY' config " "variable to be set"
            )

        app.add_url_rule("/static/meld/<path:filename>", None, self.send_static_file)

        @app.socketio.on("meld-message")
        def meld_message(message):
            """meldID, action, componentName"""
            result = process_message(message)
            app.socketio.emit("meld-response", result)
