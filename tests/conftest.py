import pytest
from flask import Flask
from flask_meld import Meld


@pytest.fixture(scope='module')
def init_app():
    meld = Meld()
    app = Flask(__name__)
    app.secret_key = __name__
    meld.init_app(app)
    return app


@pytest.fixture(scope='module')
def app(tmpdir_factory, init_app):
    # create directory structure of project/meld/components
    app_dir = tmpdir_factory.mktemp('meld')
    create_test_component(app_dir)
    init_app.config["MELD_COMPONENT_DIR"] = f"{app_dir}/meld/components"

    return init_app


@pytest.fixture(scope='module')
def app_factory(tmpdir_factory, init_app):
    # create directory structure of project/app/meld/components
    app_dir = tmpdir_factory.mktemp('app')
    create_test_component(app_dir)
    init_app.config["MELD_COMPONENT_DIR"] = f"{app_dir}/meld/components"

    return init_app


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


def write_component_class_contents(component_file):
    with component_file.open('w') as f:
        class_def = ["from flask_meld.component import Component",
                     "class Search(Component):",
                     "\tstate=''"]
        f.writelines(f"{line}\n" for line in class_def)


def create_test_component(app_dir):
    app_dir = app_dir.mkdir('meld').mkdir('components')
    component = app_dir.join("search.py")
    write_component_class_contents(component)
    return app_dir
