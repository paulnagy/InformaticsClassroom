from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo

OhdsiGroups=sorted(['Vocab', 'CDM','PLP','PLE',
'HADES','Data Quality','Pheno','ATLAS','Clin Trials','FHIR & OMOP',
'GIS','Devices','Imaging','NLP','Registry','Vaccine','Health Equity',
'Surgery','Onc','Psych','Africa','Asia Pacific','Latin Am',
'Early Stage','Open Source','Health Systems','Ed','Steering'
])

class AnswerForm(FlaskForm):
    class_name = StringField('Class',
                           validators=[DataRequired(),Length(min=2, max=25)])
    module = StringField('Module',
                        validators=[DataRequired()])
    team = StringField('Team Name',
                        validators=[DataRequired()])
    question_num = StringField('Question Number',
                        validators=[DataRequired()])
    answer_num = StringField('Answer',
                        validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

class OHDSIForm(FlaskForm):

    wg1 = SelectField('Working Group 1', choices=OhdsiGroups)
    wg2 = SelectField('Working Group 2', choices=OhdsiGroups)
    submit = SubmitField('Submit New Connection')

class ExerciseForm(FlaskForm):
    exercise=HiddenField("Field 1")

