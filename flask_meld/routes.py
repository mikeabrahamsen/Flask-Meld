from flask import render_template, request, jsonify, current_app
from .component import get_component_class
from jinja2 import nodes
from jinja2.ext import Extension

class MeldViewError(Exception):
    pass

""" TODO THIS IS UNUSED """

def _set_property_from_payload(component, payload, data):
    """
    Sets properties on the component based on the payload.
    Also updates the data dictionary which gets set back as part of the payload.
    Args:
        param component: Component to set attributes on.
        param payload: Dictionary that comes with request.
        param data: Dictionary that gets sent back with the response.
    """

    property_name = payload.get("name")
    property_value = payload.get("value")
    component.updating(property_name, property_value)

    if property_name is not None and property_value is not None:
        """
        Handles nested properties. For example, for the following component:
        class Author(MeldField):
            name = "Neil"
        class TestView(ornView):
            author = Author()

        `payload` would equal `{'name': 'author.name', 'value': 'Neil Gaiman'}`
        The following code updates UnicornView.author.name based the payload's `author.name`.
        """
        property_name_parts = property_name.split(".")
        component_or_field = component
        data_or_dict = data  # Could be an internal portion of data that gets set

        for (idx, property_name_part) in enumerate(property_name_parts):
            if hasattr(component_or_field, property_name_part):
                if idx == len(property_name_parts) - 1:
                    if hasattr(component_or_field, "_set_property"):
                        # Can assume that `component_or_field` is a component
                        component_or_field._set_property(
                            property_name_part, property_value
                        )
                    else:
                        # Handle calling the updating/updated method for nested properties
                        property_name_snake_case = property_name.replace(".", "_")
                        updating_function_name = f"updating_{property_name_snake_case}"
                        updated_function_name = f"updated_{property_name_snake_case}"

                        if hasattr(component, updating_function_name):
                            getattr(component, updating_function_name)(property_value)

                        setattr(component_or_field, property_name_part, property_value)

                        if hasattr(component, updated_function_name):
                            getattr(component, updated_function_name)(property_value)

                    data_or_dict[property_name_part] = property_value
                else:
                    component_or_field = getattr(component_or_field, property_name_part)
                    data_or_dict = data_or_dict.get(property_name_part, {})
            elif isinstance(component_or_field, dict):
                if idx == len(property_name_parts) - 1:
                    component_or_field[property_name_part] = property_value
                    data_or_dict[property_name_part] = property_value
                else:
                    component_or_field = component_or_field[property_name_part]
                    data_or_dict = data_or_dict.get(property_name_part, {})

    component.updated(property_name, property_value)
