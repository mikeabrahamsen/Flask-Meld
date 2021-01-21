from jinja2 import nodes
from jinja2.ext import Extension
from flask import url_for
from .component import get_component_class


class MeldTag(Extension):
    """
    Create a {% meld %} tag.
    Used as {% meld 'component_name' %}
    """

    tags = {"meld"}

    def parse(self, parser):
        lineno = parser.stream.expect("name:meld").lineno

        component = parser.parse_expression()

        call = self.call_method("_render", [component], lineno=lineno)
        return nodes.Output([nodes.MarkSafe(call)]).set_lineno(lineno)

    def _render(self, component):
        mn = MeldNode(component)
        return mn.render()


class MeldScriptsTag(Extension):
    """
    Create a {% meld_scripts %} tag.
    Used to add the necessary js files to init meld
    """

    tags = {"meld_scripts"}

    def parse(self, parser):
        lineno = parser.stream.expect("name:meld_scripts").lineno

        call = self.call_method("_render", lineno=lineno)
        return nodes.Output([nodes.MarkSafe(call)]).set_lineno(lineno)

    def _render(self):
        files = ["morphdom-umd.js", "socket.io.js"]
        msg_url = "message"
        base_js_url = "/meld_js_src"
        scripts = ""
        for f in files:
            url = f"{base_js_url}/{f}"
            scripts += f'<script src="{url}"></script>'

        meld_url = f"{base_js_url}/meld.js"
        meld_import = f'import {{Meld}} from "{meld_url}";'
        scripts += f'<script type="module" src="{meld_url}"></script>'
        scripts += (
            '<script type="module">'
            f'var url = "{msg_url}"; {meld_import} Meld.init(url); </script>'
        )

        return scripts


class MeldNode:
    def __init__(self, component):
        self.component_name = component

    def render(self):
        Component = get_component_class(self.component_name)
        component = Component()
        rendered_component = component.render(self.component_name)

        return rendered_component
