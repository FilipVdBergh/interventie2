from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.models import db, QuestionSet, Process, User, Question, Answer, Selection, Option, Tag, Worksession, Instrument, InstrumentTagAssignment
from interventie2.classes import Advisor

present = Blueprint('present', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


@present.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('error/index.html', title='Werksessie ontbreekt', message='Deze pagina hoort niet toegankelijk te zijn.')

@present.route('/create_new_process')
@login_required
def create_beta_process():
    # This function is opnly used to update the live database to add the new processes.
    if not (Process.query.filter_by(name='Dynamisch').first()):
        new_process = Process(name='Dynamisch')
        db.session.add(new_process)
        db.session.commit()
        print('Created new process')

    return redirect(url_for('main.index'))

@present.route('/<int:worksession_id>', methods=['GET', 'POST'])
@login_required
def present_session(worksession_id):
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
         return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    worksession = Worksession.query.get(worksession_id)
    advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
    
    return render_template('present/present.html', worksession=worksession, advisor=advisor)  

@present.route('/<int:worksession_id>/<int:question_id>', methods=['GET', 'POST'])
@login_required
def show_question(worksession_id, question_id):
    question = Question.query.get(question_id)
    worksession = Worksession.query.get(worksession_id)
    return render_template('present/focus_question.html', question=question, worksession=worksession)


@present.route('/<int:worksession_id>/update', methods=['GET', 'POST'])
@login_required
def update(worksession_id):
    if request.method == "POST":
        worksession = Worksession.query.get(worksession_id)
        if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
            return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
        
        advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
        current_question = None 

        # Each for contains options for a single question, but which question?
        for item, value in request.form.items():
            if 'question_id' in item:
                current_question = Question.query.get ( int(value) )
                break

        motivation = ''
        answer = Answer.query.filter_by(worksession=worksession, question=current_question).first()
        if answer:
            motivation = answer.motivation
            db.session.delete(answer)
        
        answer = Answer(worksession=worksession, question=current_question, motivation=motivation)

        # Add new selection
        weights = {}
        for item, value in request.form.items():
			# De name-attribute van de textarea bevat het soort vraag (motivation, option), een :::, en dan het vraagnummer of het optienummer.
            if 'option' in item:
                answer.selection.append( Selection(answer=answer, option=Option.query.get(value) ))
            if 'weight' in item:
                _, question_id = item.split(':::', 1)
                weights[int(question_id)] = value

        db.session.add(answer) 
        db.session.commit()

        return render_template('present/instruments.html', worksession=worksession, advisor=advisor)



@present.route('/<int:worksession_id>/update_motivation', methods=['GET', 'POST'])
@login_required
def update_motivation(worksession_id):
     if request.method == "POST":
        worksession = Worksession.query.get(worksession_id)
        if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
            return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

        current_question = None 

        # Each for contains options for a single question, but which question?
        for item, value in request.form.items():
            if 'question_id' in item:
                current_question = Question.query.get ( int(value) )
                break

        answer = Answer.query.filter_by(worksession=worksession, question=current_question).first()

        for item, value in request.form.items():
			# De name-attribute van de textarea bevat het soort vraag (motivation, option), een :::, en dan het vraagnummer of het optienummer.
            if 'motivation' in item:
                answer.motivation = value
        
        db.session.commit()

        return ""
     
     
@present.route('/<int:worksession_id>/uncheck_options', methods=['GET', 'POST'])
@login_required
def uncheck_options(worksession_id):
     if request.method == "POST":
        worksession = Worksession.query.get(worksession_id)
        if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
            return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

        advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
        current_question = None 

        # Each for contains options for a single question, but which question?
        for item, value in request.form.items():
            if 'question_id' in item:
                current_question = Question.query.get ( int(value) )
                break

        answer = Answer.query.filter_by(worksession=worksession, question=current_question).first()

        motivation = ''
        answer = Answer.query.filter_by(worksession=worksession, question=current_question).first()
        
        if answer:
            motivation = answer.motivation
            db.session.delete(answer)
        
        answer = Answer(worksession=worksession, question=current_question, motivation=motivation)
        db.session.add(answer) 
        db.session.commit()

        return render_template('present/instruments.html', worksession=worksession, advisor=advisor)
     

@present.route('/<int:worksession_id>/summarize_answer/<int:question_id>')
@login_required
def summarize_answer(worksession_id, question_id):
    worksession = Worksession.query.get(worksession_id)
    question = Question.query.get(question_id)
    answer = Answer.query.filter_by(worksession=worksession).filter_by(question=question).first()

    if answer is None:
        return ""

    return render_template('present/answer_summary.html', answer=answer)


@present.route('/<int:worksession_id>/question_set')
@login_required
def show_question_set(worksession_id):
    worksession = Worksession.query.get(worksession_id)
    return render_template('present/questionnaire.html', worksession=worksession)


@present.route('/<int:worksession_id>/instrument/<int:instrument_id>')
@login_required
def show_instrument(worksession_id, instrument_id):
    worksession = Worksession.query.get(worksession_id)
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
    instrument = Instrument.query.get(instrument_id)
    return render_template('present/explanation.html', worksession=worksession, instrument=instrument, advisor=advisor)