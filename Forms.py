from wtforms import Form, StringField, validators, IntegerField, DateField, SelectField
import datetime


class CreateClientForm(Form):
    Name = StringField('Client Name', [validators.DataRequired()])
    Patron = IntegerField('Pledged Amount/month', default=0)
    Word_Bank = IntegerField("Current Word Bank", default=0)
    Registered = DateField("Registration of Patron", default=datetime.date(2005,5,18))

class UpdateClientForm(Form):
    Name = StringField('Client Name')
    Total_Commissioned = IntegerField('Total Words Commissioned')
    Patron = IntegerField('Pledged Amount/month')
    Word_Bank = IntegerField("Current Word Bank")
    Registered = DateField("Registration of Patron", default=None)

class CreateCommissionsForm(Form):
    Story = StringField('Story Name', [validators.DataRequired()])
    Name = SelectField('Client Name', [validators.DataRequired()], choices= " ")
    Word_Count = IntegerField("Word Count (Mark it as thousands)", default=0)
    
class UpdateCommissionsForm(Form):
    Story = StringField('Story Name',)
    Name = SelectField('Client Name', choices= " ", default="")
    Word_Count = IntegerField("Word Count (Mark it as thousands)", default=0)
    Progress = IntegerField("Words Written Already")
    Status = SelectField('Status', choices= " ", default="")