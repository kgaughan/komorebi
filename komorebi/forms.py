from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired


class EntryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    link = URLField("Link")
    via = URLField("Via")
    note = TextAreaField("Note")
