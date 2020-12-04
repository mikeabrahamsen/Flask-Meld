import pytest
from flask import Flask
from flask_meld import Meld


@pytest.fixture(scope='module')
def app(tmpdir_factory):
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
def client(app):
    return app.test_client()


@pytest.yield_fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx
