from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


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

# RuntimeConfigurationsForm to configure source configurations
# RuntimeConfigurationsForm to configure target configurations
class DynamicForm(FlaskForm):
    pass  # We will dynamically add fields

class SourceConfigurationForm(FlaskForm):
    submit = SubmitField('Submit')


# CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
