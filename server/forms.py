import arrow
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField, DateTimeField, SelectField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, EqualTo
from config import settings
from utils import Logger

log = Logger()

class SerialTXForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])

class DeviceSettingsForm(FlaskForm):
    device_id = StringField('Device Id', validators=[DataRequired()]) 
    name = StringField('Name', validators=[DataRequired()])

class DBPurgeDeviceReadingsForm(FlaskForm):
    devices = SelectMultipleField('Devices', choices=[])
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])

class DBPurgeReadingsForm(FlaskForm):
    reged = BooleanField('All Registered Devices (ignore devices list above)')
    unreg = BooleanField('All Unregistered Devices (ignore devices list above)')
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])

class DBPurgeRegistryForm(FlaskForm):
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])

class DBPurgeLogsForm(FlaskForm):
    start = DateTimeField('Start', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End', default=arrow.utcnow(), validators=[])
    cats = SelectMultipleField('Categories', choices=[])
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])

class AreYouSureForm(FlaskForm):
    confirm = BooleanField('Confirm', validators=[DataRequired()])

class LogFilterForm(FlaskForm):
    start = DateTimeField('Start', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End', default=arrow.utcnow().shift(hours=+1), validators=[])
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
    messurement = SelectField('Dataset',choices=settings.INFLUX_MESSUREMENTS, default=settings.INFLUX_MESSUREMENTS[0][0])


class ReadingForm(FlaskForm):
    utc = DateTimeField('UTC', default=arrow.utcnow(), validators=[])
    device_id = StringField('Device ID',  validators=[DataRequired()])
    field = StringField('Field name',  validators=[DataRequired()])
    dtype = SelectField('Data Type', choices=[('float','float'), ('int','int'), ('bool','bool'), ('string','string'), ('percent','percent')], validators=[])
    unit  = StringField('Unit of messurement', validators=[DataRequired()])
    value = StringField('Value', validators=[DataRequired()])