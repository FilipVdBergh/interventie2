from interventie2 import app, login_manager
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.session import make_transient
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash, check_password_hash
import random

db = SQLAlchemy(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def generate_secret_key():
        return ''.join((random.choice('QWERTYUIOPASDFGHJKLZXCVBNM1234567890') for i in range(20)))


def clone(obj, worksession):
    # remove the object from the worksession (set its state to detached)
    worksession.expunge(obj)
    # make it transient (set its state to transient)
    make_transient(obj)
    # now set all primary keys to None so there are no conflicts later
    for pk in inspect(obj).mapper.primary_key:
        setattr(obj, pk.name, None)
    return obj

class Role(db.Model):
    __tablename__  = 'roles'
    id             = db.Column(db.Integer, primary_key=True) #1=root 2=admin, 3=maintainer, 4=user, 5=demo
    name           = db.Column(db.String(20), nullable=False, unique=True)
    see_app_info   = db.Column(db.Boolean)
    see_all_worksessions = db.Column(db.Boolean)
    edit_catalog   = db.Column(db.Boolean)
    edit_questionnaire = db.Column(db.Boolean)
    edit_users     = db.Column(db.Boolean)
    demo           = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(80), nullable=False, unique=True)
    password      = db.Column(db.String(200), nullable=False)
    role_id       = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=4) #references roles.id
    description   = db.Column(db.String(2000), nullable=False, default="")
    email         = db.Column(db.String(254))
    link          = db.Column(db.String(1000))
    active        = db.Column(db.Boolean, nullable=False, default=True)
    date_created  = db.Column(db.DateTime(timezone=True), server_default=func.now())
    last_seen     = db.Column(db.DateTime(timezone=True), server_default=func.now())

    role = relationship('Role')
    worksession = relationship('Worksession', back_populates='creator')
    allowed_worksessions = relationship('Worksession', secondary='worksession_access', back_populates='allowed_users')
    owned_instruments = relationship('Instrument', back_populates='owner')
    
    def edit_allowed(self):
        if not current_user.is_authenticated:
            return False
        elif self.role.id == 1 and current_user.role.id != 1:
            # Only root can edit root.
            return False
        elif current_user.role.edit_users:
            return True
        elif current_user == self:
            return True
        else:
            return False
    def set_password(self, password):
        self.password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)
    def __repr__(self):
        return f'<User {self.name}>'


class Worksession(db.Model):
    __tablename__ = 'worksessions'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    date_modified = db.Column(db.DateTime(timezone=True), server_default=func.now())
    parent_id     = db.Column(db.Integer, db.ForeignKey('worksessions.id'))
    child_description = db.Column(db.String(2000), nullable=False, default="")
    participants  = db.Column(db.String(500), nullable=False, default="")
    date          = db.Column(db.String(100))
    description   = db.Column(db.String(2000), nullable=False, default="")
    effect        = db.Column(db.String(2000), nullable=False, default="")
    conclusion    = db.Column(db.String(2000), nullable=False, default="")
    link_to_page  = db.Column(db.String(1000))
    show_instruments = db.Column(db.Boolean, default=True)
    mark_top_instruments = db.Column(db.Integer, nullable=False, default=1)
    show_rest_instruments = db.Column(db.Boolean, default=False)
    show_tags     = db.Column(db.Boolean, default=True)
    presenter_mode_zoom = db.Column(db.Numeric(3,2), nullable=False, default=1.25)
    presenter_mode_color_title = db.Column(db.String(7))
    presenter_mode_text_color_title = db.Column(db.String(7))
    presenter_mode_color_nav = db.Column(db.String(7))
    presenter_mode_text_color = db.Column(db.String(7))
    presenter_mode_text_color_nav = db.Column(db.String(7))
    presenter_mode_color_coll = db.Column(db.String(7))
    presenter_mode_text_color_coll = db.Column(db.String(7))
    presenter_mode_color_highlight = db.Column(db.String(7))
    presenter_mode_text_color_highlight = db.Column(db.String(7))
    presenter_mode_text_color_heading = db.Column(db.String(7))
    presenter_mode_background_color1 = db.Column(db.String(7))
    presenter_mode_background_color2 = db.Column(db.String(7))
    archived      = db.Column(db.Boolean, default=False)
    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'))
    process_id    = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False, default=1)
    creator_id    = db.Column(db.Integer, db.ForeignKey('users.id')) #references users.id
    secret_key    = db.Column(db.String(20), nullable=False, default=generate_secret_key())

    parent = relationship('Worksession', remote_side=[id], backref='children')
    creator = relationship('User', back_populates='worksession')
    allowed_users = relationship('User', secondary='worksession_access', back_populates='allowed_worksessions')
    answers = relationship('Answer', back_populates='worksession', cascade='all, delete-orphan')
    question_set = relationship('QuestionSet')
    process = relationship('Process')


    def is_option_selected(self, option):
        """Use this function to find out if a particular option is checked in this worksession."""
        for answer in self.answers:
            for selection in answer.selection:
                if option == selection.option:
                    return True
        return False


    def active_tags(self):
        """Returns a list of all active tags."""
        active_tags = []
        for answer in self.answers:
            for selection in answer.selection:
                for tag in selection.option.tags:
                    active_tags.append(tag)
        return active_tags
    

    def active_tags_alt(self):
        """The previous function has a problem. If a question that is ordinarily hidden is answered while visible, and later made hidden,
        the tag is still active. The above function cannot use the is_question_hidden function, because that function requires calling
        the above function for active tags."""
        active_tags = []
        return active_tags


    def is_question_hidden(self, question):
        """This function determines if a question is hidden based on the current question set and the active tags
        (as some questions may require a tag to be active in the worksession)."""
        if not question in self.question_set.questions:
            return True # Hidden: question is not a part of the question set of this worksession.
       
        if len(question.required_active_tags) == 0:
            return False # Not hidden: the question has no required active tags so is always shown.

        for tag in question.required_active_tags:
            if tag in self.active_tags():
                return False # Not hidden: required tag was found to be active
            else:
                pass
                       
        return True

    
    def get_weight(self, question):
        for answer in self.answers:
            if answer.question == question:
                return answer.weight

    def __repr__(self):
        return f'<Worksession {self.name}>'


WorksessionAccess = db.Table('worksession_access',
                            db.Column('id', db.Integer, primary_key=True),
                            db.Column('worksession_id', db.Integer, db.ForeignKey('worksessions.id')),
                            db.Column('user_id', db.Integer, db.ForeignKey('users.id')))


class Instrument(db.Model):
    __tablename__ = 'instruments'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False, unique=True)
    date_created  = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_modified = db.Column(db.DateTime(timezone=True), server_default=func.now())
    introduction  = db.Column(db.String(2000), nullable=False, default="")
    description   = db.Column(db.String(2000), nullable=False, default="")
    referenced_elsewhere = db.Column(db.Boolean)
    reference_link = db.Column(db.String(1000))
    considerations = db.Column(db.String(2000), nullable=False, default="")
    examples      = db.Column(db.String(2000), nullable=False, default="")
    links         = db.Column(db.String(2000), nullable=False, default="")
    owner_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) #references users.id
    
    owner = relationship('User', back_populates='owned_instruments')
    tags = relationship('InstrumentTagAssignment', back_populates='instrument', cascade='all, delete-orphan')
    remarks = relationship('Remark', back_populates='instrument', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Instrument {self.name}>'


class Remark(db.Model):
    __tablename__ = 'remarks'
    id            = db.Column(db.Integer, primary_key=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'))
    date_created  = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_modified = db.Column(db.DateTime(timezone=True), server_default=func.now())
    remark        = db.Column(db.String(2000), nullable=False, default="")
    sender_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    active        = db.Column(db.Boolean)
    instrument = relationship('Instrument')
    sender = relationship('User')

    def edit_allowed(self):
        if not current_user.is_authenticated:
            return False
        return (current_user.role.edit_catalog or current_user == self.sender)
    def __repr__(self):
        return f'<Remark {self.remark}>'


class Tag(db.Model):
    __tablename__ = 'tags'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False, unique=True)

    instruments = relationship('InstrumentTagAssignment', back_populates='tag', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tag {self.name}>'


class InstrumentTagAssignment(db.Model):
    __tablename__ = 'instrument_tags'
    id            = db.Column(db.Integer, primary_key=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'), nullable=False)  #reference instruments.id
    tag_id        = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)  #reference tagsid
    weight        = db.Column(db.Numeric(2,1), nullable=False, default=1.0)
    multiplier    = db.Column(db.Numeric(2,1), nullable=False, default=1.0)

    instrument = relationship('Instrument', back_populates='tags')
    tag = relationship('Tag', back_populates='instruments')

    def __repr__(self):
        return f'<InstrumentTagItem Instrument {self.instrument}-Tag {self.tag}>'


class Option(db.Model):
    __tablename__ = 'options'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(500), nullable=False)
    order         = db.Column(db.Integer, nullable=False, default=100)
    question_id   = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False) #reference questions.id

    question = relationship('Question', back_populates='options')
    tags = relationship('Tag', secondary='option_tags')

    def __repr__(self):
        return f'<Option {self.name}>'


OptionTagAssignment = db.Table('option_tags',
                            db.Column('id', db.Integer, primary_key=True),
                            db.Column('option_id', db.Integer, db.ForeignKey('options.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))


class Question(db.Model):
    __tablename__ = 'questions'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(500), nullable=False)
    description   = db.Column(db.String(2000), nullable=False, default="")
    question_set_id = db.Column(db.Integer, db.ForeignKey('question_sets.id'))  #references question_sets.id
    allow_motivation = db.Column(db.Boolean, nullable=False, default=True)
    allow_choice  = db.Column(db.Boolean, nullable=False, default=True)
    allow_multiselect = db.Column(db.Boolean, nullable=False, default=False)
    allow_weight  = db.Column(db.Boolean, nullable=False, default=False)
    order         = db.Column(db.Integer, nullable=False, default=100)

    required_active_tags = relationship('Tag', secondary='question_required_tags')
    options = relationship('Option', cascade='all, delete-orphan')
    question_set = relationship('QuestionSet', back_populates='questions')
    
    @hybrid_property
    def is_category(self):
        return (not(self.allow_motivation or self.allow_choice))
       
    def __repr__(self):
        return f'<Question {self.name}>'

QuestionRequiredTagsAssignment = db.Table('question_required_tags',
                            db.Column('id', db.Integer, primary_key=True),
                            db.Column('question_id', db.Integer, db.ForeignKey('questions.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))


class QuestionSet(db.Model):
    __tablename__ = 'question_sets'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(500), nullable=False)
    description   = db.Column(db.String(2000), nullable=False, default="")
    owner_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) #references users.id
    date_created  = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_modified = db.Column(db.DateTime(timezone=True), server_default=func.now())
    default_process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False, default=1)
    default_instruments_visible = db.Column(db.Boolean, nullable=False, default=True)
    default_tags_visible = db.Column(db.Boolean, nullable=False, default=False)
    default_allow_weights = db.Column(db.Boolean, nullable=False, default=False)
    
    forbidden_tags = relationship('Tag', secondary='question_set_forbidden_tags')
    mandatory_tags = relationship('Tag', secondary='question_set_mandatory_tags')
    owner = relationship('User')
    default_process = relationship('Process')    
    questions = relationship('Question', cascade='all, delete-orphan')
    worksessions = relationship('Worksession', back_populates='question_set', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<QuestionSet {self.name}>'


ForbiddenTagAssignment = db.Table('question_set_forbidden_tags',
                            db.Column('id', db.Integer, primary_key=True),
                            db.Column('question_set_id', db.Integer, db.ForeignKey('question_sets.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))


MandatoryTagAssignment = db.Table('question_set_mandatory_tags',
                            db.Column('id', db.Integer, primary_key=True),
                            db.Column('question_set_id', db.Integer, db.ForeignKey('question_sets.id')),
                            db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')))


class Process(db.Model):
    __tablename__  = 'processes'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f'<Process {self.name}>'


class Answer(db.Model):
    __tablename__ = 'answers'
    id            = db.Column(db.Integer, primary_key=True)
    worksession_id    = db.Column(db.Integer, db.ForeignKey('worksessions.id'), nullable=False) #references worksessions.id
    question_id   = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False) #references questions.id
    motivation    = db.Column(db.String(2000), nullable=False, default="")
    weight        = db.Column(db.Numeric(2,1), nullable=False, default=1.0)
    inherit_answers = db.Column(db.Boolean, nullable=False, default=False)

    worksession = relationship('Worksession')
    question = relationship('Question')
    selection = relationship('Selection', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Answer Worksession {self.worksession}-Question{self.question}>'


class Selection(db.Model):
    __tablename__ = 'selections'
    id            = db.Column(db.Integer, primary_key=True)
    answer_id     = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False) #references answers.id
    option_id     = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=False) #references options.id
    multiplier    = db.Column(db.Numeric(2,1), nullable=False, default=1.0) # The multiplier is not implemented!
    
    answer = relationship('Answer', back_populates='selection', cascade='all, delete')
    option = relationship('Option')

    def __repr__(self):
        return f'<Selection Answer {self.answer}-Option{self.option}>'
