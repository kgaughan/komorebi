from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, URLField
from wtforms.validators import DataRequired


class EntryForm(FlaskForm):
    class Meta:
        csrf = False

    title = StringField("Title", validators=[DataRequired()])
    link = URLField("Link")
    via = URLField("Via")
    note = TextAreaField("Note")
