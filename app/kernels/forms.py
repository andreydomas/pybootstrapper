from flask.ext.wtf import Form, DataRequired, FileField

class KernelForm(Form):
    kernel =FileField('Kernel', validators=[DataRequired()])
