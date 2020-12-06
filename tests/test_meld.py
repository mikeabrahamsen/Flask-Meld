from flask_meld.component import get_component_class


def test_module_load_with_app_factory(app_factory_ctx):
    component_class = get_component_class("search")
    assert component_class.__name__ == "Search"


def test_module_load_with_single_file_app(app_ctx):
    component_class = get_component_class("search")
    assert component_class.__name__ == "Search"
