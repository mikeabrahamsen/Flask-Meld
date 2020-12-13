from .component import get_component_class


def process_message(message):
    meld_id = message["id"]
    action = message["action"]
    component_name = message["componentName"]
    meld_id = meld_id

    data = message["data"]
    Component = get_component_class(component_name)
    component = Component(meld_id, **data)
    payload = action["payload"]

    if "syncInput" in action["type"]:
        if hasattr(component, payload["name"]):
            setattr(component, payload["name"], payload["value"])

    elif "callMethod" in action["type"]:
        data = message["data"]
        call_method_name = payload.get("name", "")
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
                params = params_str.split(",")

        if method_name is not None and hasattr(component, method_name):
            func = getattr(component, method_name)

            if params:
                func(*params)
            else:
                func()
    rendered_component = component.render(component_name)

    res = {"id": meld_id, "dom": rendered_component, "data": component._attributes()}
    return res
