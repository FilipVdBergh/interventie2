from flask import Blueprint, current_app, render_template, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.models import db, generate_secret_key, Question, Answer, Selection, Option, Worksession, Instrument, Votes, Plan, InstrumentChoice
from interventie2.forms import EditCaseForm
from interventie2.classes import Advisor
from datetime import datetime, timedelta
from interventie2.admin.routes import send_system_message

present = Blueprint('present', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


@present.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('error/index.html', title='Werksessie ontbreekt', message='Deze pagina hoort niet toegankelijk te zijn.')


@present.route('/<int:worksession_id>/question_visibility')
@login_required
def question_visibility(worksession_id):
    """This function returns a JOSN-object of the question_id and the display-tag based on the visibility of the question."""
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
        return None
    
    resp = { }

    worksession = Worksession.query.get(worksession_id)
    for question in worksession.question_set.questions:
        # attribute = 'display'
        # value = "none" if worksession.is_question_hidden(question) else "block"
        
        attribute = 'opacity'
        value = "20%" if worksession.is_question_hidden(question) else "100%"


        resp.update({ f'question_container_{question.id}': {attribute: value } })

    return resp

@present.route('/<int:worksession_id>/frontpage', methods=['GET', 'POST'])
@login_required
def frontpage(worksession_id):
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
         return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    worksession = Worksession.query.get(worksession_id)
    form = EditCaseForm()

    if form.validate_on_submit():
        worksession.description = form.description.data
        worksession.effect = form.effect.data
        db.session.commit()
        return redirect(url_for('present.present_session', worksession_id=worksession.id))
    elif request.method == "GET":
        form.description.data = worksession.description 
        form.effect.data = worksession.effect
    
    return render_template('present/frontpage.html', worksession=worksession, form=form)  



@present.route('/<int:worksession_id>', methods=['GET', 'POST'])
@login_required
def present_session(worksession_id):
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
         return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    worksession = Worksession.query.get(worksession_id)
    advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
    
    return render_template('present/present.html', worksession=worksession, advisor=advisor)  



@present.route('/<int:worksession_id>/<int:question_id>/options', methods=['GET', 'POST'])
@login_required
def show_options(worksession_id, question_id):
    question = Question.query.get(question_id)
    worksession = Worksession.query.get(worksession_id)
    votes = Votes.query.filter_by(worksession=worksession, question=question).all()
    
    return render_template('present/options.html', question=question, worksession=worksession, votes=votes)



@present.route('/<int:worksession_id>/update', methods=['GET', 'POST'])
@login_required
def update(worksession_id):
    if request.method == "POST":
        worksession = Worksession.query.get(worksession_id)
        if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
            return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
        
        # advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
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
        # weights = {}

        for item, value in request.form.items():
            print(f'item: {item}, value: {value}')
			# De name-attribute van de textarea bevat het soort vraag (motivation, option), een :::, en dan het vraagnummer of het optienummer.
            if 'option' in item:
                answer.selection.append( Selection(answer=answer, option=Option.query.get(value) ))        
            # if 'weight' in item:
            #     _, question_id = item.split(':::', 1)
            #     weights[int(question_id)] = value
        db.session.add(answer) 
        db.session.commit()
        
        advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
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


@present.route('/<int:worksession_id>/active_tags')
@login_required
def show_active_tags(worksession_id):
    worksession = Worksession.query.get(worksession_id)
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
    advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())

    return render_template('present/active_tags.html', worksession=worksession, advisor=advisor)



@present.route('/<int:worksession_id>/instrument/<int:instrument_id>')
@login_required
def show_instrument(worksession_id, instrument_id):
    worksession = Worksession.query.get(worksession_id)
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    instrument = Instrument.query.get(instrument_id)
    return render_template('present/instrument.html', worksession=worksession, instrument=instrument)


@present.route('/<int:worksession_id>/instrument_details/<int:instrument_id>')
@login_required
def show_explanation(worksession_id, instrument_id):
    worksession = Worksession.query.get(worksession_id)
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

    instrument = Instrument.query.get(instrument_id)
    advisor = Advisor(worksession=worksession, instruments=instrument)

    return render_template('present/instrument_details.html', 
                           worksession=worksession, 
                           instrument=instrument, 
                           instrument_calculation=advisor.explain_score(instrument))


@present.route('/<int:worksession_id>/conclusion', methods=['GET', 'POST'])
@login_required
def conclusion(worksession_id):
    worksession = Worksession.query.get(worksession_id)
    advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())

    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	# Create an interventionplan based on the finished worksession if one doesn't exist
	# A plan is a selection of instruments relevant to a worksession, with some motivation.
	# A worksession can have multiple plans, but plan 0 os always the one made immediately after
	# the session. This way, the actually executed plan can also be stored in the database.

    plan = Plan.query.filter_by(worksession_id=worksession.id).filter_by(stage=0).first()
		# Stage = 0 is always the primary conclusion after finishing a worksession
    if  plan is None:
        plan = Plan(worksession=worksession,
			  stage=0,
			  description="Interventieplan aangemaakt na de werksessie",
			  conclusion="") # I actually don't understand why the value can ever be None, but it is.

    if request.method == "POST":
		#Store the conclusion with the plan.
        plan.conclusion = request.form.get("motivation")

        db.session.add(plan)
        db.session.commit()

        # return redirect(url_for('main.show_worksession', worksession_id=worksession.id))

    return render_template('/present/conclusion.html', worksession=worksession, advisor=advisor, plan=plan)


@present.route('/<int:worksession_id>/update_conclusion', methods=['GET', 'POST'])
@login_required
def update_conclusion(worksession_id):
    if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
    
    worksession = Worksession.query.get(worksession_id)
    plan = Plan.query.filter_by(worksession_id=worksession.id).filter_by(stage=0).first()
            # Stage = 0 is always the primary conclusion after finishing a worksession
    if  plan is None:
        plan = Plan(worksession=worksession,
            stage=0,
            description="Interventieplan aangemaakt na de werksessie",
            conclusion=request.form.get("motivation"))
    else:
        plan.conclusion = request.form.get("motivation")

        db.session.add(plan)
        db.session.commit()
    
    return plan.conclusion





@present.route('/<int:worksession_id>/instrument/<int:instrument_id>/<int:score>', methods=['GET', 'POST'])
@login_required
def update_instrument_checkbox(worksession_id, instrument_id, score):
    if request.method == "POST":
        worksession = Worksession.query.get(worksession_id)
        if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
            return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

        current_instrument = Instrument.query.get(instrument_id)
        plan = Plan.query.filter_by(worksession_id=worksession.id).filter_by(stage=0).first()
            # Stage = 0 is always the primary conclusion after finishing a worksession
        if  plan is None:
            plan = Plan(worksession=worksession,
                stage=0,
                description="Interventieplan aangemaakt na de werksessie",
                conclusion="") # I actually don't understand why the value can ever be None, but it is.
            db.session.add(plan)
        
        
        for item, value in request.form.items():
            if 'instrument_id' in item:
                instrument = Instrument.query.get(value)
        if request.form.getlist('choose_instrument'):
            # Write instrument to intervention plan
            instrument_choice = InstrumentChoice(plan=plan, instrument=instrument)
            db.session.add(instrument_choice)
        else:
            # Delete instrument from intervention plan if present
            # There is only one possibible hit, I hope
            instrument_choice = InstrumentChoice.query.filter_by(plan=plan, instrument=instrument).first() 
            db.session.delete(instrument_choice)

        db.session.commit()

        return current_instrument.name