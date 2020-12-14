from flask_meld.component import Component


class ExampleComponent(Component):
    test_var = "test"
    test_var_2 = 12

    def test_method(self):
        return "method_test"


def test_component_variables_are_valid():
    component = ExampleComponent()
    expected_attributes = ["errors", "test_var", "test_var_2"]
    assert list(component._attributes().keys()) == expected_attributes


def test_component_methods_are_valid():
    component = ExampleComponent()
    expected_methods = ["test_method"]
    assert list(component._functions().keys()) == expected_methods
