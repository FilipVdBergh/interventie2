from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField, EmailField, BooleanField, DecimalField, RadioField, IntegerField, SelectMultipleField, DateField
from wtforms.widgets import ColorInput, CheckboxInput
from wtforms.validators import DataRequired, DataRequired, Length, ValidationError, Email, Optional, EqualTo, NumberRange
from interventie2.models import User

class RegisterForm(FlaskForm):
    name        = StringField('Naam', validators=[DataRequired(), Length(min=2, max=80)], render_kw={'placeholder': 'Naam', 'size': 100})
    password    = PasswordField('Wachtwoord', validators=[DataRequired(), Length(min=4, max=80), EqualTo('password_match', message='Wachtwoorden moeten gelijk zijn.')], render_kw={'placeholder': 'Wachtwoord', 'size': 40})
    password_match = PasswordField('Herhaal wachtwoord', validators=[DataRequired(), Length(min=4, max=80)], render_kw={'placeholder': 'Herhaal wachtwoord', 'size': 40})
    role        = SelectField('Rol', default=4)
    email       = EmailField('E-mail', validators=[Optional(), Length(max=254), Email()], render_kw={'placeholder':'e-mailadres', 'size': 100})
    description = TextAreaField('Omschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    link        = StringField('Link naar een persoonlijke pagina', validators=[Optional(), Length(max=1000)], render_kw={'size': 100})
    submit      = SubmitField('Maak nieuwe gebruiker')

    def validate_name(self, name):
        user = User.query.filter_by(name=name.data).first()
        if user is not None:
            raise ValidationError('Deze naam is al in gebruik. Kies een nieuwe naam.')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Dit e-mailadres is al in gebruik. Kies een ander e-mailadres.')


class ChangePasswordForm(FlaskForm):
    password    = PasswordField('Wachtwoord', validators=[DataRequired(), Length(min=4, max=80), EqualTo('password_match', message='Wachtwoorden moeten gelijk zijn.')], render_kw={'placeholder': 'Wachtwoord', 'size': 40})
    password_match = PasswordField('Herhaal wachtwoord', validators=[DataRequired(), Length(min=4, max=80)], render_kw={'placeholder': 'Herhaal wachtwoord', 'size': 40})
    submit      = SubmitField('Wijzig wachtwoord')


class EditUserForm(FlaskForm):
    name        = StringField('Naam', validators=[DataRequired(), Length(min=2, max=80)], render_kw={'size': 100})
    role        = SelectField('Rol', coerce=int)
    email       = EmailField('E-mail', validators=[Optional(), Length(max=254), Email()], render_kw={'size': 100})
    description = TextAreaField('Omschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    link        = StringField('Link naar persoonlijke pagina', validators=[Optional(), Length(max=1000)], render_kw={'size': 100})
    submit      = SubmitField('Opslaan')


class SendSystemMessageForm(FlaskForm):
    subject            = StringField('Onderwerp', validators=[Optional(), Length(min=1, max=500)], render_kw={'size': 100})
    body               = TextAreaField('Bericht', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    deliver_after      = DateField('Datum verzending', format='%Y-%m-%d')
    submit             = SubmitField('Verzenden')


class SendMessageForm(FlaskForm):
    subject            = StringField('Onderwerp', validators=[Optional(), Length(min=1, max=500)], render_kw={'size': 100})
    body               = TextAreaField('Bericht', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    submit             = SubmitField('Verzenden')


class LoginForm(FlaskForm):
    name        = StringField('Naam', validators=[DataRequired()], render_kw={'placeholder': 'Naam'})
    password    = PasswordField('Wachtwoord', validators=[DataRequired()], render_kw={'placeholder': 'Wachtwoord'})
    submit      = SubmitField('Log in')


class InstrumentsForm(FlaskForm):
    name               = StringField('Naam', validators=[DataRequired(), Length(min=2, max=100)], render_kw={'size': 100})
    introduction       = TextAreaField('Inleiding', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    description        = TextAreaField('Beschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    referenced_elsewhere = BooleanField('Beschrijving buiten deze app', validators=[], default=False)
    reference_link     = StringField('Link naar beschrijving buiten deze app', validators=[Optional(), Length(max=1000)], render_kw={'size': 100})
    considerations     = TextAreaField('Overwegingen', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    examples           = TextAreaField('Voorbeelden', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    links              = TextAreaField('Links', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    owner              = SelectField('Eigenaar', coerce=int)
    submit             = SubmitField('Instrument opslaan')


class RemarkForm(FlaskForm):
    remark             = TextAreaField('Opmerking', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    closed             = BooleanField('Afgesloten', default=False)
    submit             = SubmitField('Opmerking opslaan')


class TagForm(FlaskForm):
    name               = StringField('Naam', validators=[DataRequired(), Length(min=2, max=100)], render_kw={'size': 40})
    submit             = SubmitField('Tag opslaan')


class TagInstrumentAssignmentForm(FlaskForm):
    tag                = SelectField('Tag', coerce=int)
    type               = SelectField('Soort', coerce=int)
    multiplier         = DecimalField('Factor', places=1)
    weight             = DecimalField('Gewicht', validators=[NumberRange(max=5)], places=1)
    submit             = SubmitField('Opslaan')


class QuestionSetForm(FlaskForm):
    name               = StringField('Naam', validators=[DataRequired(), Length(min=2, max=500)], render_kw={'size': 100})
    description        = TextAreaField('Omschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    owner              = SelectField('Eigenaar', coerce=int)
    default_process    = SelectField('Standaardproces', coerce=int)
    default_instruments_visible = BooleanField('Laat standaard de instrumentenlijst zien bij het invullen van de tool', validators=[], default=True)
    default_tags_visible = BooleanField('Laat standaard de actieve tags zien bij het invullen van de tool', validators=[], default=False)
    default_allow_weights = BooleanField('Sta vragen met weging standaard toe', validators=[], default=False)
    color              = StringField('Achtergrondkleur', widget=ColorInput(), default='#f7f5f0')
    text_color         = StringField('Tekstkleur', widget=ColorInput(), default='#000000')
    submit             = SubmitField('Tool opslaan')


class AddQuestionForm(FlaskForm):
    name               = StringField('Vraag', validators=[DataRequired(), Length(min=2, max=500)], render_kw={'size': 100})
    submit             = SubmitField('Opslaan')


class QuestionForm(AddQuestionForm):
    description        = TextAreaField('Omschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100}) 
    allow_motivation   = BooleanField('Motivatie vragen', validators=[], default=True)
    allow_choice       = BooleanField('Meerkeuzevraag stellen', validators=[], default=True)    
    allow_multiselect  = BooleanField('Meerdere opties op meerkeuzevraag toestaan', validators=[], default=False)
    allow_weight       = BooleanField('Gewicht bij vraag toestaan', validators=[], default=False)


class OptionForm(FlaskForm):
    name               = StringField('Antwoordoptie', validators=[DataRequired(), Length(min=2, max=500)], render_kw={'size': 100})
    submit             = SubmitField('Toevoegen')


class AddTagToQuestionSet(FlaskForm):
    tag                = SelectField('Tag', coerce=int)
    #submit             = SubmitField('Toevoegen') # Weggehaald en in HTML opgelost omdat dit formlier twee maal op de pagina staat, en dat gaat mis met validatie.


class AddRequiredTagToQuestionForm(FlaskForm):
    tag                = SelectField('Tag', coerce=int)
    submit             = SubmitField('Toevoegen')

class NewWorksessionForm(FlaskForm):
    name               = StringField('Naam werksessie', validators=[DataRequired(), Length(min=2, max=500)], render_kw={'size': 100})
    project_number     = StringField('Projectnummer',   validators=[Optional(), Length(max=500)], render_kw={'size': 100})
    participants       = TextAreaField('Deelnemers', validators=[Optional(), Length(max=500)], render_kw={'rows': 5, 'cols': 100})
    date               = DateField('Datum werksessie', format='%Y-%m-%d')
    link_to_page       = StringField('Link naar projectpagina', validators=[Optional(), Length(max=1000)], render_kw={'size': 100})
    question_set       = SelectField('Keuzetool', validators=[DataRequired()], coerce=int)
    submit             = SubmitField('Werksessie opslaan')


class EditWorksessionForm(FlaskForm):
    name               = StringField('Naam werksessie', validators=[DataRequired(), Length(min=2, max=500)], render_kw={'size': 100})
    project_number     = StringField('Projectnummer',   validators=[Optional(), Length(max=500)], render_kw={'size': 100})
    participants       = TextAreaField('Deelnemers', validators=[Optional(), Length(max=500)], render_kw={'rows': 5, 'cols': 100})
    link_to_page       = StringField('Link naar projectpagina', validators=[Optional(), Length(max=1000)], render_kw={'size': 100})
    date               = DateField('Datum werksessie', format='%Y-%m-%d')
    choice_process     = SelectField('Keuzeproces', coerce=int)
    description        = TextAreaField('Beschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100})
    show_instruments   = BooleanField('Laat de instrumentenlijst zien', validators=[], default=True)
    mark_top_instruments = IntegerField('Aanbevolen instrumenten', validators=[NumberRange(min=0)], default=1)
    show_rest_instruments = BooleanField('Laat instrumenten onder de top ook zien', validators=[], default=True)
    show_tags          = BooleanField('Laat de actieve tags zien', validators=[], default=True)
    presenter_mode_zoom                 = DecimalField('Zoomfactor', validators=[NumberRange(min=1, max=2.5)], places=2)
    presenter_mode_color_title          = StringField('Kleur titelbalkbalk', widget=ColorInput(), default='#000000')
    presenter_mode_text_color_title     = StringField('Kleur titelbalktekst', widget=ColorInput(), default='#DDDDDD')
    presenter_mode_color_nav            = StringField('Kleur navigatiebalk', widget=ColorInput(), default='#BBBBBB')
    presenter_mode_text_color_nav       = StringField('Kleur navigatiebalktekst', widget=ColorInput(), default='#BBBBBB')
    presenter_mode_color_coll           = StringField('Kleur uitklapveld', widget=ColorInput(), default='#BBBBBB')
    presenter_mode_text_color_coll      = StringField('Kleur uitklapveldtekst', widget=ColorInput(), default='#BBBBBB')
    presenter_mode_color_highlight      = StringField('Kleur selectie', widget=ColorInput(), default='#BBBBBB')
    presenter_mode_text_color_highlight = StringField('Kleur selectietekst', widget=ColorInput(), default='#BBBBBB')
    presenter_mode_text_color_heading   = StringField('Kleur koptekst', widget=ColorInput(), default='#0000FF')
    presenter_mode_text_color           = StringField('Kleur tekst', widget=ColorInput(), default='#000000')    
    presenter_mode_background_color1    = StringField('Achtergrondkleur (boven)', widget=ColorInput(), default='#FFFFFF')
    presenter_mode_background_color2    = StringField('Achtergrondkleur (onder)', widget=ColorInput(), default='#DDDDDD')
    archived           = BooleanField('Archiveer deze werksessie', validators=[], default=False)
    submit             = SubmitField('Werksessie opslaan')


class EditCaseForm(FlaskForm):
    description        = TextAreaField('Omschrijving', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100})
    effect             = TextAreaField('Beoogd doel', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100})
    submit             = SubmitField('Opslaan')


class EditConclusionForm(FlaskForm):
    conclusion         = TextAreaField('Conclusie', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100})
    submit             = SubmitField('Opslaan')


class MarkdownPlaygroundForm(FlaskForm):
    playground         = TextAreaField('Tekst', validators=[Optional(), Length(max=4000)], render_kw={'rows': 60, 'cols': 60})
    submit             = SubmitField('Bekijken')


class EditWorksessionAccessForm(FlaskForm):
    user               = SelectMultipleField('Gebruiker', coerce=int)
    submit             = SubmitField('Toevoegen')


# class CloneWorksessionForm(FlaskForm):


class ExportWorksessionForm(FlaskForm):
    remarks                = TextAreaField('Opmerkingen bij export', validators=[Optional(), Length(max=2000)], render_kw={'rows': 10, 'cols': 100})
    export_descriptions    = BooleanField('Neem beschrijvingen van instrumenten op in de export', validators=[], default=True)
    export_calculations    = BooleanField('Neem berekeningen van instrumentscores op in de export', validators=[], default=False)
    export_all_instruments = BooleanField('Neem alle instrumenten op in de export, en niet alleen de hoogst scorende', validators=[], default=False)
    export_tags            = BooleanField('Neem actieve tags op in de export', validators=[], default=False)
    export_technical_info  = BooleanField('Neem technische info van de app op in de export', validators=[], default=False)
    submit                 = SubmitField('Exporteren')
