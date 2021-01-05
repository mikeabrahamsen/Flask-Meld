import pytest

from flask_meld.message import parse_call_method_name


@pytest.mark.parametrize(["message_name", "expected_params"], [
    ("call(hello)", ["hello"]),
    ("call('hello')", ["hello"]),
    ("call('hello, world')", ["hello, world"]),
    ("call(hello, world)", ["hello", "world"]),
    ("call(1)", [1]),
    ("call(1, 2)", [1, 2]),
    ("call(1, 2, 'hello')", [1, 2, "hello"]),
    # ("call(1, 2, hello)", [1, 2, "hello"]), # should this be supported?
])
def test_parse(message_name, expected_params):
    method_name, params = parse_call_method_name(message_name)
    assert method_name == 'call'
    assert params == expected_params
