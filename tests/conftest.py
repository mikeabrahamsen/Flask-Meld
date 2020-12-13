import pytest
from flask import Flask
from flask_meld import Meld
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec


def init_app(app_dir):
    meld = Meld()
    app = Flask(app_dir)
    app.secret_key = __name__
    meld.init_app(app)
    return app


@pytest.fixture(scope="module")
def app(tmpdir_factory):
    # create directory structure of project/meld/components
    app_dir = tmpdir_factory.mktemp("project", numbered=False)
    meld = Meld()
    app = Flask(f"{app_dir}")
    create_test_component(app_dir)
    app.secret_key = __name__
    meld.init_app(app)
    return app


@pytest.fixture(scope="module")
def app_factory(tmpdir_factory):
    # create directory structure of project/app/meld/components
    project_dir = tmpdir_factory.mktemp("app_factory_project", numbered=False)
    Path(f"{project_dir}/app").mkdir(parents=True, exist_ok=True)
    app_dir = Path(f"{project_dir}/app")

    create_test_component(f"{app_dir}")
    factory_init = Path(f"{app_dir}/__init__.py")
    write_init_contents(factory_init)
    spec = spec_from_file_location(f"{app_dir}", f"{app_dir}/__init__.py")
    test = module_from_spec(spec)
    spec.loader.exec_module(test)

    app = test.create_app("test_config")
    return app


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)


@pytest.fixture
def client(app_factory):
    return app_factory.test_client()


@pytest.fixture
def app_factory_ctx(app_factory):
    with app_factory.app_context() as ctx:
        yield ctx


@pytest.fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx


def create_test_component(app_dir):
    Path(f"{app_dir}/meld/components").mkdir(parents=True, exist_ok=True)
    component = Path(f"{app_dir}/meld/components/search.py")
    write_component_class_contents(component)
    return app_dir


def write_component_class_contents(component_file):
    with component_file.open("w") as f:
        class_def = [
            "from flask_meld.component import Component",
            "class Search(Component):",
            "\tstate=''",
        ]
        f.writelines(f"{line}\n" for line in class_def)


def write_init_contents(factory_init):
    with factory_init.open("w") as f:
        class_def = [
            "from flask import Flask",
            "from flask_meld import Meld",
            "meld = Meld()",
            "def create_app(config_name):",
            "\tapp = Flask(__name__)",
            '\tapp.config["SECRET_KEY"] = "super_secret_test_key"',
            "\tmeld.init_app(app)",
            "\treturn app",
        ]
        f.writelines(f"{line}\n" for line in class_def)
