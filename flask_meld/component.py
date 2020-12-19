import uuid
import os
from importlib.util import module_from_spec, spec_from_file_location

import orjson
from flask import render_template, current_app, url_for
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter


def convert_to_snake_case(s):
    s.replace("-", "_")
    return s


def convert_to_camel_case(s):
    s = convert_to_snake_case(s)
    return "".join(word.title() for word in s.split("_"))


def get_component_class(component_name):
    module_name = convert_to_snake_case(component_name)
    class_name = convert_to_camel_case(module_name)
    module = get_component_module(module_name)
    component_class = getattr(module, class_name)

    return component_class


def get_component_module(module_name):
    user_specified_dir = current_app.config.get("MELD_COMPONENT_DIR", None)

    if not user_specified_dir:
        try:
            name = getattr(current_app, "name", None)
            full_path = os.path.join(name, "meld", "components", module_name + ".py")
            module = load_module_from_path(full_path, module_name)
        except FileNotFoundError:
            full_path = os.path.join("meld", "components", module_name + ".py")
            module = load_module_from_path(full_path, module_name)
        return module
    else:
        try:
            full_path = os.path.join(user_specified_dir, module_name + ".py")
            module = load_module_from_path(full_path, module_name)
        except FileNotFoundError:
            full_path = os.path.join(
                user_specified_dir, "components", module_name + ".py"
            )
            module = load_module_from_path(full_path, module_name)
        return module


def load_module_from_path(full_path, module_name):
    spec = spec_from_file_location(module_name, full_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CSRF_TOKEN_ATTR = "csrf_token"


class Component:
    def __init__(self, id=None, **kwargs):
        if not id:
            id = uuid.uuid4()
        self.errors = {}
        self._form = None
        self.__dict__.update(**kwargs)
        self.id = id

        if hasattr(self, "form_class"):
            self._bind_form(kwargs)

    def __repr__(self):
        return f"<meld.Component {self.__class__.__name__}-vars{self._attributes()})>"

    @property
    def _meld_attrs(self):
        """
        A list of meld variables and functions that are hidden from the view
        """
        return ["id", "render", "validate", "updated"]

    def _bind_form(self, kwargs):
        """
        Create a form from the form_class, add meld:model to each field and
        bind kwargs to field data
        """
        # tricky: https://flask-wtf.readthedocs.io/en/stable/api.html
        # need to pass formdata=None or flask-wtf will try to use the
        # flask request object to populate the form
        self._form = getattr(self, "form_class")(formdata=None)
        for field in self._form:
            meld_attribute = {"meld:model": field.name}
            setattr(self._form[field.name], "render_kw", meld_attribute)
            self._bind_data_to_form(field, kwargs)

    def _set_token(self, field):
        """
        Gather the CSRF token from the form and apply it to the component.
        """
        soup = BeautifulSoup(field.__call__(), features="html.parser")
        token = soup.find(attrs={"name": CSRF_TOKEN_ATTR}).get("value")
        self.csrf_token = token

    def _bind_data_to_form(self, field, kwargs):
        """
        Bind any attributes from kwargs that are form fields to the form.
        """
        if field.name in kwargs:
            self._set_field_data(field.name, kwargs[field.name])
            if field.name == CSRF_TOKEN_ATTR:
                self._set_token(field)
        else:
            setattr(self, field.name, None)

    def _set_field_data(self, field_name, value):
        """
        Set the data attribute on a form field.
        """
        setattr(self._form[field_name], "data", value)

    def validate(self, field=None):
        """
        Validate a form or a field.
        """
        if not self._form:
            return True

        if field:
            validate = field.validate(self._form)
        else:
            validate = self._form.validate()

        if not validate:
            for field in self._form:
                if field.errors:
                    self.errors[field.name] = field.errors
        return validate

    def _attributes(self):
        """
        Get attributes that can be called in the component.
        """
        attributes = {}

        attributes_names = [
            attr
            for attr in dir(self)
            if not callable(getattr(self, attr))
            and not attr.startswith("_")
            and attr not in self._meld_attrs
        ]
        for name in attributes_names:
            attributes[name] = getattr(self, name)

        return attributes

    def _functions(self):
        """
        Get methods that can be called in the component.
        """

        functions = {}

        function_list = [
            func
            for func in dir(self)
            if callable(getattr(self, func))
            and not func.startswith("_")
            and func not in self._meld_attrs
        ]

        for func in function_list:
            functions[func] = getattr(self, func)

        return functions

    def __context__(self):
        """
        Collects every thing that could be used in the template context.
        """
        return {
            "attributes": self._attributes(),
            "methods": self._functions(),
        }

    def updated(self, name):
        """
        Hook that gets called when a component's data is about to get updated.
        """
        pass

    def render(self, component_name):
        return self._view(component_name, self._attributes())

    def _view(self, component_name, data):
        context = self.__context__()
        context_variables = {}
        context_variables.update(context["attributes"])
        context_variables.update(context["methods"])
        context_variables.update(data)
        context_variables.update({"form": self._form})

        frontend_context_variables = {}
        frontend_context_variables.update(context["attributes"])
        frontend_context_variables = orjson.dumps(frontend_context_variables).decode(
            "utf-8"
        )

        rendered_template = render_template(
            f"meld/{component_name}.html", **context_variables
        )

        soup = BeautifulSoup(rendered_template, features="html.parser")
        root_element = Component._get_root_element(soup)
        root_element["meld:id"] = str(self.id)
        root_element["meld:data"] = frontend_context_variables
        self._set_values(root_element, context_variables)

        script = soup.new_tag("script", type="module")
        init = {"id": str(self.id), "name": component_name, "data": data}
        init = orjson.dumps(init).decode("utf-8")

        meld_url = url_for("static", filename="meld/meld.js")
        meld_import = f'import {{Meld}} from ".{meld_url}";'
        script.string = f"{meld_import} Meld.componentInit({init});"
        root_element.append(script)

        rendered_template = Component._desoupify(soup)

        return rendered_template

    def _set_values(self, soup, context_variables):
        """
        Set the value on model fields
        """
        for element in soup:
            try:
                if "meld:model" in element.attrs:
                    element.attrs["value"] = context_variables[
                        element.attrs["meld:model"]
                    ]
            except Exception:
                # There are cases where an element will not have attrs and does not need
                # to be set. Simply ignore those
                pass

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
