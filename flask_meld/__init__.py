from flask import send_from_directory
import os

from jinja2 import nodes
from jinja2.ext import Extension

from .component import get_component_class

from flask_socketio import SocketIO


__version__ = '0.0.3'


class Meld(object):
    def __init__(self, app=None):
        self.app = app

        if app is not None:
            self.init_app(app)

    def send_static_file(self, filename):
        _static_dir = os.path.realpath(
            os.path.join(os.path.dirname(__file__), 'static/js'))
        """Send a static file from the flask-meld static directory."""
        return send_from_directory(_static_dir, filename)

    def init_app(self, app):
        app.jinja_env.add_extension(MeldExtension)
        app.jinja_env.add_extension(MeldScriptsExtension)
        app.socketio = SocketIO(app)

        if not app.config.get('SECRET_KEY'):
            raise RuntimeError(
                "The Flask-Meld requires the 'SECRET_KEY' config "
                "variable to be set")

        app.add_url_rule('/_meld/static/js/<path:filename>', None,
                         self.send_static_file)

        @app.socketio.on('message')
        def meld_message(message):
            """ meldID, action, componentName
            """
            result = process_message(message)
            app.socketio.emit('response', result)

        def process_message(message):
            meld_id = message["id"]
            action = message["action"]
            component_name = message["componentName"]
            meld_id = meld_id

            Component = get_component_class(component_name)
            component = Component(meld_id)
            payload = action["payload"]

            if 'syncInput' in action["type"]:
                if hasattr(component, payload['name']):
                    setattr(component, payload['name'], payload['value'])

            elif "callMethod" in action["type"]:
                data = message["data"]
                call_method_name = payload.get("name", "")
                method_name = call_method_name

                for arg in component.__attributes__():
                    try:
                        value = data.get(arg)
                        setattr(component, arg, value)

                    except ValueError:
                        pass
                    except AttributeError as e:
                        print(f"{e}: {arg}-{value}")

                method_name = call_method_name
                params = None

                if "(" in call_method_name and call_method_name.endswith(")"):
                    param_idx = call_method_name.index("(")
                    params_str = call_method_name[param_idx:]

                    # Remove the arguments from the method name
                    method_name = call_method_name.replace(params_str, "")

                    # Remove parenthesis
                    params_str = params_str[1:-1]
                    if params_str == "":
                        return method_name
                    else:
                        params = params_str.split(',')

                if method_name is not None and hasattr(component, method_name):
                    func = getattr(component, method_name)

                    if params:
                        func(*params)
                    else:
                        func()
            rendered_component = component.render(component_name)

            res = {
                "id": meld_id,
                "dom": rendered_component,
                "data": component.__attributes__()
            }
            return res


class MeldScriptsExtension(Extension):
    """
    Create a {% meld_scripts %} tag.
    Used to add the necessary js files to init meld
    """

    tags = {'meld_scripts'}

    def parse(self, parser):
        lineno = parser.stream.expect('name:meld_scripts').lineno

        call = self.call_method('_render', lineno=lineno)
        return nodes.Output([nodes.MarkSafe(call)]).set_lineno(lineno)

    def _render(self):
        files = ["morphdom-umd.js", "meld.js", "socket.io.js"]
        msg_url = "message"
        scripts = ""
        for f in files:
            scripts += f'<script src="_meld/static/js/{f}"></script>'

        scripts += f'<script>var url = "{msg_url}"; Meld.init(url); </script>'

        return scripts


class MeldExtension(Extension):
    """
    Create a {% meld %} tag.
    Used as {% meld 'component_name' %}
    """

    tags = {'meld'}

    def parse(self, parser):
        lineno = parser.stream.expect('name:meld').lineno

        component = parser.parse_expression()

        call = self.call_method('_render', [component], lineno=lineno)
        return nodes.Output([nodes.MarkSafe(call)]).set_lineno(lineno)

    def _render(self, component):
        mn = MeldNode(component)
        return mn.render()


class MeldNode():
    def __init__(self, component):
        self.component_name = component

    def render(self):
        Component = get_component_class(self.component_name)
        component = Component()
        rendered_component = component.render(self.component_name)

        return rendered_component
