from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.validators import DataRequired, URL, Email
from streamsets_manager import StreamSetsManager


# RegisterForm to register new users
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


# LoginForm to login existing users
class LoginForm(FlaskForm):
    username = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let's Go !!")

# TemplateForm to pick ingestion pattern
class TemplateForm(FlaskForm):
    source = SelectField('Source', choices=[('', 'Source...')], validators=[DataRequired()])
    destination = SelectField('Destination', choices=[('', 'Destination...')], validators=[DataRequired()])
    submit = SubmitField('Next: Runtime Configurations')

# # RuntimeConfigurationsForm to configure source/target configurations
# class DynamicForm(FlaskForm):
#     pass  # We will dynamically add fields


class FormGenerator:
    @staticmethod
    def generate_form(string_fields_dict, job_template_id, submit_text):
        class DynamicForm(FlaskForm):
            pass

        streamsets_manager = StreamSetsManager()
        job_template_static_params = streamsets_manager.get_job_template_static_params(job_template_id)
        # Dynamically add StringFields using dictionary keys as labels and values as default values
        for label, default_value in string_fields_dict.items():
            if label in job_template_static_params:
                # disable static input fields
                setattr(DynamicForm, label, StringField(label, render_kw={'disabled': 'disabled'}, default=default_value, validators=[DataRequired()]))
            else:
                setattr(DynamicForm, label, StringField(label, default=default_value, validators=[DataRequired()]))
            setattr(DynamicForm, submit_text, SubmitField(submit_text))
        return DynamicForm

# Form to pick Job Instance Suffix
class JobInstanceSuffixForm(FlaskForm):
    instance_name_suffix = SelectField('Instance Name Suffix:', choices=[('default', 'Select a suffix')], validators=[DataRequired()])
    suffix_parameter_name = SelectField('Parameter Name:', choices=[('default', 'Parameter...')], validators=[DataRequired()])
    submit = SubmitField('Submit Job')

