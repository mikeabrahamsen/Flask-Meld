import importlib
import inspect
import uuid

import orjson
from flask import render_template
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter


def convert_to_snake_case(s):
    # TODO: Better handling of dash->snake
    s.replace("-", "_")
    return s


def convert_to_camel_case(s):
    # TODO: Better handling of dash/snake->camel-case
    s = convert_to_snake_case(s)
    return "".join(word.title() for word in s.split("_"))


def get_component_class(component_name):
    # TODO: Handle the module not being found
    module_name = convert_to_snake_case(component_name)
    module = importlib.import_module(f"meld.components.{module_name}")

    # TODO: Handle the class not being found
    class_name = convert_to_camel_case(module_name)
    component_class = getattr(module, class_name)

    return component_class


class Component:
    def __init__(self, id=None):
        if not id:
            id = uuid.uuid4()

        self.id = id
        self._data = {}

    def __repr__(self):
        return f"<meld.Component {self.__class__.__name__}-vars{self.__attributes__()})>"

    def __attributes__(self):
        """
        Get attributes that can be called in the component.
        """
        non_callables = [
            member[0] for member in inspect.getmembers(self, lambda x: not callable(x))
        ]
        attribute_names = list(
            filter(lambda name: Component._is_public_name(name), non_callables,)
        )

        attributes = {}

        for attribute_name in attribute_names:
            attributes[attribute_name] = object.__getattribute__(self, attribute_name)

        return attributes

    def __methods__(self):
        """
        Get methods that can be called in the component.
        """

        # TODO: Should only take methods that only have self argument?
        member_methods = inspect.getmembers(self, inspect.ismethod)
        public_methods = filter(
            lambda method: Component._is_public_name(method[0]), member_methods
        )
        methods = {k: v for (k, v) in public_methods}

        return methods

    def __context__(self):
        """
        Collects every thing that could be used in the template context.
        """
        return {
            "attributes": self.__attributes__(),
            "methods": self.__methods__(),
        }

    @property
    def _item_data(self):
        return self._data

    @_item_data.setter
    def _item_data(self, data):
        self._data = data

    def render(self, component_name):
        return self.view(component_name, self._data)

    def view(self, component_name, data):
        context = self.__context__()
        context_variables = {}
        context_variables.update(context["attributes"])
        context_variables.update(context["methods"])
        context_variables.update(data)

        frontend_context_variables = {}
        frontend_context_variables.update(context["attributes"])
        frontend_context_variables = orjson.dumps(frontend_context_variables).decode(
            "utf-8"
        )

        rendered_template = render_template(f'meld/{component_name}.html', **context_variables)

        soup = BeautifulSoup(rendered_template, features="html.parser")
        root_element = Component._get_root_element(soup)
        root_element["meld:id"] = str(self.id)
        root_element["meld:data"] = frontend_context_variables
        self.set_values(root_element, context_variables)

        script = soup.new_tag("script")
        init = {
            "id": str(self.id),
            "name": component_name,
        }
        init = orjson.dumps(init).decode("utf-8")
        script.string = f"Meld.componentInit({init});"
        root_element.append(script)

        rendered_template = Component._desoupify(soup)

        return rendered_template

    def set_values(self, soup, context_variables):
        for element in soup:
            try:
                if "meld:model" in element.attrs:
                    element.attrs["value"] = context_variables[element.attrs["meld:model"]]
            except Exception as e:
                pass

    @staticmethod
    def _is_public_name(name):
        """
        Determines if the name should be sent in the context.
        """
        protected_names = (
            "id",
            "render",
            "view",
        )
        return not (name.startswith("_") or name in protected_names)

    @staticmethod
    def _get_root_element(soup):
        for element in soup.contents:
            if element.name:
                return element

        raise Exception("No root element found")

    @staticmethod
    def _desoupify(soup):
        soup.smooth()
        return soup.encode(formatter=UnsortedAttributes()).decode("utf-8")


class UnsortedAttributes(HTMLFormatter):
    """
    Prevent beautifulsoup from re-ordering attributes.
    """

    def attributes(self, tag):
        for k, v in tag.attrs.items():
            yield k, v
