from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.models import db, QuestionSet, Process, User, Question, Answer, Selection, Option, Tag, Worksession, Instrument, InstrumentTagAssignment, Votes
from interventie2.classes import Advisor

vote = Blueprint('vote', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


@vote.route('/')
@login_required
def index():
    return render_template('error/index.html', title='Werksessie ontbreekt', message='Deze pagina hoort niet toegankelijk te zijn.')


@vote.route('/<int:worksession_id>/<voting_key>', methods=['GET', 'POST'])
@login_required
def touch_vote(worksession_id, voting_key):
    # if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
    #     return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    worksession = Worksession.query.get(worksession_id)

    if not worksession.enable_voting:
        return render_template('vote/not_allowed.html')
    if not worksession.voting_key == voting_key:
        return render_template('vote/key_expired.html')
   
    return render_template('vote/vote.html', worksession=worksession)


@vote.route('/<int:worksession_id>show_question/<int:question_id>')
@login_required
def show_question(worksession_id, question_id):
    worksession = Worksession.query.get(worksession_id)
    question = Question.query.get(question_id)
    votes = Votes.query.filter_by(worksession=worksession, question=question,user=current_user)

    return render_template('vote/question.html', worksession=worksession, question=question, votes=votes)


@vote.route('/<int:worksession_id>/update', methods=['GET', 'POST'])
@login_required
def update(worksession_id):
    worksession = Worksession.query.get(worksession_id)
    current_question = None 

    # Each for contains options for a single question, but which question?
    for item, value in request.form.items():
        if 'question_id' in item:
            current_question = Question.query.get ( int(value) )
            break

    # Clear all previous user votes for this worksession and question
    all_votes = Votes.query.filter_by(worksession_id=worksession.id, user_id=current_user.id, question_id=current_question.id).all()
    for vote in all_votes:
        db.session.delete(vote)

    # Create new votes
    for item, value in request.form.items():
        # De name-attribute van de textarea bevat het soort vraag (motivation, option), een :::, en dan het vraagnummer of het optienummer.
        if 'option' in item:
            vote = Votes(worksession_id=worksession.id, user_id=current_user.id, question_id=current_question.id, option=Option.query.get(value) )
            db.session.add(vote)

    db.session.commit()

    return ""