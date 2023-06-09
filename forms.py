#lambda/forms.py
from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, SubmitField, SelectField)
from flask_ckeditor import CKEditorField
from wtforms.validators import (InputRequired,NumberRange, Length)


class ConfigurationForm(FlaskForm):
    stock = StringField('Which company stock?',validators=[InputRequired()])
    select_service = SelectField('Service', choices=[
                            ('lambda', 'Lambda'),
                            ('emr', 'EMR')])
    resource_number = IntegerField('Number of resource used in parallel', validators=[InputRequired(),NumberRange(1,8)])
    history = IntegerField('Length of price history (as days)', validators=[InputRequired(),NumberRange(4,10000)])
    shots = IntegerField('Shots for calculating risk', validators=[InputRequired(),NumberRange(1,50000)])
    select_signal = SelectField('Signal', choices=[
                            ('buy', 'BUY'),
                            ('sell', 'SELL')])
    days_past = IntegerField('Number of days after which to check profit/loss', validators=[InputRequired(),NumberRange(1,10000)])
    submit = SubmitField('Submit')

class CreditForm(FlaskForm):
        content = CKEditorField('Enter Your AWS Credential', validators=[Length(max=1000)])
        submit = SubmitField('Proceed to Config')