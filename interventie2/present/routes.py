from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.models import User
from interventie2.models import db, QuestionSet, Process, User, Question, Answer, Option, Tag, Worksession, Instrument, InstrumentTagAssignment
from interventie2.classes import Advisor

present = Blueprint('present', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


@present.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('error/index.html', title='Werksessie ontbreekt', message='Deze pagina hoort niet toegankelijk te zijn.')



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



# @main.route('/worksession/<int:worksession_id>/present', methods=['GET', 'POST'])
# @main.route('/worksession/<int:worksession_id>/present/<int:question_id>', methods=['GET', 'POST'])
# @login_required
# def present(worksession_id, question_id=None):
# 	worksession = Worksession.query.get(worksession_id)
# 	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
# 		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
# 	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
# 	if question_id is None:
# 		question = Question.query.filter_by(question_set=worksession.question_set).order_by(Question.order).first()
# 	else:	
# 		question = Question.query.get(question_id)
# 	answer = Answer.query.filter_by(worksession=worksession, question=question).first()
	
# 	if request.method == "POST":
# 		for answer in Answer.query.filter_by(worksession=worksession):
# 			# Delete all answers to replace them below.
# 			for selection in answer.selection:
# 				db.session.delete(selection)
# 			db.session.delete(answer)

# 		motivations = {}
# 		selected_options = []
# 		weights = {}
# 		for item, value in request.form.items():
# 			# De name-attribute van de textarea bevat het soort vraag (motivation, option), een :, en dan het vraagnummer of het optienummer.
# 			if 'motivation' in item:
# 				_, question_id = item.split(':', 1)
# 				motivations[int(question_id)] = value
# 			if 'option' in item:
# 				selected_options.append(int(value))
# 			if 'weight' in item:
# 				_, question_id = item.split(':', 1)
# 				weights[int(question_id)] = value

# 		for question in worksession.question_set.questions:
# 		# Alleen de vragen in de huidige question set
# 			if not question.is_category:
# 				new_answer = Answer(worksession=worksession, question=question, motivation=motivations.get(question.id), weight=weights.get(question.id))
# 				for option in question.options:
# 					if option.id in selected_options: 
# 						# De vraag zit in de huidige question set en moet aangevinkt worden.
# 						new_answer.selection.append(Selection(option=option))
# 				db.session.add(new_answer)
# 		db.session.commit()
# 		return redirect(url_for('main.present', worksession_id=worksession.id))
# 	return render_template('main/present.html', 
# 						worksession=worksession,
# 						current_question=question,
# 						advisor=advisor)