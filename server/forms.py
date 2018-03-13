import arrow
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField, DateTimeField, SelectField, IntegerField
from wtforms.validators import DataRequired, EqualTo
from utils.influx import INFLUX_MESSUREMENTS

class DeviceSettingsForm(FlaskForm):
    device_id = StringField('Device Id', validators=[DataRequired()]) 
    name = StringField('Name', validators=[DataRequired()])

class DBPurgeForm(FlaskForm):
    reged = BooleanField('Registered Devices')
    unreg = BooleanField('Unregistered Devices')
    logs  = BooleanField('Log Files')
    registry = BooleanField('Device Registry')
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])

class AreYouSureForm(FlaskForm):
    confirm = BooleanField('Confirm', validators=[DataRequired()])

class LogFilterForm(FlaskForm):
    start = DateTimeField('Start', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End', default=arrow.utcnow(), validators=[])
    cat = SelectField('Category',choices=[('','All')] + log.get_categories(), default='')
    limit = SelectField('Per&nbsp;Page', choices=[
        ('50', 50),
        ('250', 250),
        ('500', 500),
        ('1000', 1000)
    ], default=50)
    offset = HiddenField('Offset', default=0)
    orderby = SelectField('Order&nbsp;By', choices=[
        ('time ASC', 'Time (Old to New)'),
        ('time DESC', 'Time (New to Old)'),
    ], default='time DESC')

class BackupForm(FlaskForm):
    start = DateTimeField('Start Date', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End Date', default=arrow.utcnow(), validators=[])
    messurement = SelectField('Dataset',choices=INFLUX_MESSUREMENTS, default=INFLUX_MESSUREMENTS[0][0])