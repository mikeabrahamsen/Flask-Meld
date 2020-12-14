from flask_meld.component import Component
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo


class RegistrationForm(Form):
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[DataRequired()])
    password_confirm = PasswordField(
        ('Confirm Password'), validators=[DataRequired(),
                                          EqualTo('password')])


class FormComponent(Component):
    form_class = RegistrationForm
    email = ""
    password = ""
    password_confirm = ""


def test_component_has_form():
    component = FormComponent()
    assert component._form


def test_set_form_data():
    form_data = {"email": "test@test.com"}
    component = FormComponent()
    component._set_form_data(form_data)
    assert component._form.email.data == "test@test.com"


def test_component_sets_form_data():
    form_data = {"email": "test@test.com"}
    component = FormComponent(**form_data)
    assert component._form.email.data == "test@test.com"


def test_form_validate_is_true():
    form_data = {"email": "test@test.com",
                 "password": "somepass",
                 "password_confirm": "somepass"}
    component = FormComponent(**form_data)
    assert component.validate()


def test_form_validate_has_errors_if_failed():
    form_data = {"email": "test@test.com",
                 "password": "somepass",
                 "password_confirm": "nomatch"}
    component = FormComponent(**form_data)
    assert not component.validate()
    assert component._form.password_confirm.errors
