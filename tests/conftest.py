import pytest
from flask import Flask
from flask_meld import Meld


@pytest.fixture(scope='module')
def app(tmpdir_factory):
    # create directory structure of project/meld/components
    app_dir = tmpdir_factory.mktemp('meld')
    app_dir.mkdir('components')
    module = app_dir.join("search.py")
    with module.open('w') as f:
        class_def = ["from flask_meld.component import Component",
                     "class Search(Component):",
                     "\tstate=''"]
        f.writelines(f"{line}\n" for line in class_def)

    meld = Meld()
    app = Flask(__name__)
    app.config["MELD_COMPONENT_DIR"] = app_dir
    app.secret_key = __name__
    meld.init_app(app)
    return app


@pytest.fixture(scope='module')
def app_factory(tmpdir_factory):
    # create directory structure of project/app/meld/components
    app_dir = tmpdir_factory.mktemp('app')
    app_dir = app_dir.mkdir('meld').mkdir('components')
    module = app_dir.join("search.py")
    with module.open('w') as f:
        class_def = ["from flask_meld.component import Component",
                     "class Search(Component):",
                     "\tstate=''"]
        f.writelines(f"{line}\n" for line in class_def)

    meld = Meld()
    app = Flask(__name__)
    app.secret_key = __name__
    app.config["MELD_COMPONENT_DIR"] = app_dir

    meld.init_app(app)
    return app


@pytest.fixture
def client(app_factory):
    return app_factory.test_client()


@pytest.yield_fixture
def app_factory_ctx(app_factory):
    with app_factory.app_context() as ctx:
        yield ctx


@pytest.yield_fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx
