from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.forms import LoginForm, NewWorksessionForm, EditWorksessionForm, EditCaseForm, EditConclusionForm, MarkdownPlaygroundForm, EditWorksessionAccessForm
from interventie2.models import User, Worksession, QuestionSet, Instrument, Option, Answer, Selection, Question, Process, InstrumentChoice, Plan, Message
from interventie2.models import db, generate_secret_key
from interventie2.classes import Advisor
from sqlalchemy.sql import func
from decimal import Decimal
from datetime import datetime
from interventie2.admin.routes import send_system_message
import hashlib


main = Blueprint('main', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')




@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
	information = { "past_worksessions":  Worksession.query.filter(Worksession.date < datetime.today()).order_by(Worksession.name).count(),
				    "next_worksessions":  Worksession.query.filter(Worksession.date > datetime.today()).order_by(Worksession.name).count(),
					"instruments": Instrument.query.order_by(Instrument.name).count(),
					"your_past_worksessions":  Worksession.query.filter(Worksession.date < datetime.today()).filter(Worksession.creator == current_user).order_by(Worksession.name).count(),
				    "your_next_worksessions":  Worksession.query.filter(Worksession.date > datetime.today()).filter(Worksession.creator == current_user).order_by(Worksession.name).count(),
					"your_instruments": Instrument.query.filter(Instrument.owner == current_user).order_by(Instrument.name).count() }




	next_worksessions = Worksession.query.filter(Worksession.date > datetime.today()).order_by(Worksession.date)
	return render_template('main/index.html', 
						information=information,
						next_worksessions=next_worksessions)

@main.route('/worksessions', methods=['GET', 'POST'])
@login_required
def worksessions():
	worksessions = Worksession.query.order_by(Worksession.date)

	return render_template('main/worksessions.html', worksessions=worksessions)


@main.route('/archived')
@login_required
def archived():
	worksessions = Worksession.query.order_by(Worksession.name)
	return render_template('main/archived.html', worksessions=worksessions)


@main.route('/login', methods=['GET', 'POST'])
def login():
	# Redirect if already logged in
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(name=form.name.data).first()
		if user is None or not user.check_password(form.password.data):
			return redirect(url_for('main.login'))
		login_user(user)
		current_user.last_seen = func.now()
		return redirect(url_for('main.index'))
	return render_template('main/login.html', form=form)


@main.route('/logout')
@login_required
def logout():
	current_user.last_seen = func.now()
	db.session.add(current_user) 
	db.session.commit()
	logout_user()
	return redirect(url_for('main.index'))


@main.route('/markdown_help', methods=['GET', 'POST'])
def markdown_help():
	form = MarkdownPlaygroundForm()
	playground_text = ""

	if form.validate_on_submit():
		playground_text = form.playground.data
	elif request.method == 'GET':
		markdown_input = ""
		with main.open_resource('markdown-cheat-sheet.md') as f:
			for line in f.readlines():
				markdown_input += line.decode('utf-8')
		form.playground.data = markdown_input
	return render_template('main/markdown_help.html', form=form, playground_text=playground_text)


@main.route('/new_worksession', methods=['GET', 'POST'])
@login_required
def new_worksession():
	form = NewWorksessionForm()
	form.question_set.choices = [(question_set.id, question_set.name) for question_set in QuestionSet.query.order_by(QuestionSet.name)]

	if form.validate_on_submit():
		worksession = Worksession()
		worksession.name = form.name.data
		worksession.project_number = form.project_number.data
		worksession.link_to_page = form.link_to_page.data
		worksession.date = form.date.data
		worksession.participants = form.participants.data
		worksession.question_set_id = form.question_set.data
		worksession.creator = current_user
		worksession.show_instruments = QuestionSet.query.get(worksession.question_set_id).default_instruments_visible
		worksession.show_tags =  QuestionSet.query.get(worksession.question_set_id).default_instruments_visible
		worksession.process_id = QuestionSet.query.get(worksession.question_set_id).default_process_id
		worksession.presenter_mode_zoom = 1.00
		worksession.presenter_mode_color_title = '#FFFFFF'
		worksession.presenter_mode_text_color_title ='#000061'
		worksession.presenter_mode_color_nav = '#091e31'
		worksession.presenter_mode_text_color_nav ='#d7d7d7'
		worksession.presenter_mode_text_color_heading = '#000061'
		worksession.presenter_mode_text_color = '#000000'
		worksession.presenter_mode_color_coll = '#EEEEEE'
		worksession.presenter_mode_text_color_coll ='#000000'
		worksession.presenter_mode_color_highlight = '#65C7FF'
		worksession.presenter_mode_text_color_highlight ='#000000'
		worksession.presenter_mode_background_color1 = '#FFFFFF'
		worksession.presenter_mode_background_color2 = '#FFFFFF'
		worksession.allowed_users.append(current_user)
		worksession.archived = False
		db.session.add(worksession)
		db.session.commit()
		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))
	elif request.method == 'GET':
		pass
	return render_template('main/new_worksession.html', form=form)


@main.route('/clone_worksession/<int:worksession_id>', methods=['GET', 'POST'])
@login_required
def clone_worksession(worksession_id):
	parent_worksession = Worksession.query.get(worksession_id)

	if request.method == "POST":
		worksession = Worksession()
		worksession.name = parent_worksession.name
		worksession.project_number = parent_worksession.project_number.data
		worksession.participants = parent_worksession.participants
		worksession.date = parent_worksession.date
		worksession.description = parent_worksession.description
		worksession.effect = parent_worksession.effect
		worksession.conclusion == parent_worksession.conclusion
		worksession.question_set_id = parent_worksession.question_set_id
		worksession.creator = current_user
		worksession.show_instruments = parent_worksession.show_instruments
		worksession.show_tags =parent_worksession.show_tags
		worksession.process_id = parent_worksession.process_id
		worksession.presenter_mode_zoom = parent_worksession.presenter_mode_zoom
		worksession.presenter_mode_color_title = parent_worksession.presenter_mode_color_title
		worksession.presenter_mode_text_color_title = parent_worksession.presenter_mode_text_color_title
		worksession.presenter_mode_color_nav = parent_worksession.presenter_mode_color_nav
		worksession.presenter_mode_text_color_nav = parent_worksession.presenter_mode_text_color_nav
		worksession.presenter_mode_text_color_heading = parent_worksession.presenter_mode_text_color_heading 
		worksession.presenter_mode_text_color = parent_worksession.presenter_mode_text_color
		worksession.presenter_mode_color_coll = parent_worksession.presenter_mode_color_coll
		worksession.presenter_mode_text_color_coll = parent_worksession.presenter_mode_text_color_coll
		worksession.presenter_mode_color_highlight = parent_worksession.presenter_mode_color_highlight
		worksession.presenter_mode_text_color_highlight =parent_worksession.presenter_mode_text_color_highlight
		worksession.presenter_mode_background_color1 = parent_worksession.presenter_mode_background_color1
		worksession.presenter_mode_background_color2 = parent_worksession.presenter_mode_background_color2
		worksession.allowed_users.append(parent_worksession.creator)
		worksession.archived = False
		worksession.parent = Worksession.query.get(worksession_id)
		worksession.child_description = request.form.getlist('child_description')
		
		db.session.add(worksession)
		db.session.commit()
		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))
	elif request.method == "GET":
		pass
	return render_template('main/clone_worksession.html', worksession=parent_worksession)


@main.route('/worksession/<int:worksession_id>', methods=['GET', 'POST'])
@login_required
def show_worksession(worksession_id):
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	worksession = Worksession.query.get(worksession_id)
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	to_be_hashed = f'{date.today()}{worksession.secret_key}'
	invitation_string = hashlib.sha1(to_be_hashed.encode('utf-8')).hexdigest()

	form = EditWorksessionAccessForm()
	form.user.choices = [(user.id, user.name) for user in User.query.order_by(User.name)]

	if form.validate_on_submit():
		for user_id in form.user.data:
			worksession.allowed_users.append(User.query.get(user_id))
		db.session.commit()
	elif request.method == "GET":
		pass

	return render_template('main/worksession.html', 
						worksession=worksession, 
						advisor=advisor,
						form=form,
						invitation_string=invitation_string)


@main.route('/worksession/<int:worksession_id>/plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def show_plan(worksession_id, plan_id):
	plan = Plan.query.get(plan_id)
	worksession = plan.worksession
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	if not current_user.role.see_all_worksessions and current_user not in worksession.allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	if request.method == "POST":
		plan.description = request.form.get("plan_description")
		plan.conclusion = chosen_instruments = request.form.get("plan_motivation")
		#Erase previously selected instruments
		for instrument_choice in plan.instruments:
			db.session.delete(instrument_choice)
		#Store all checked instruments
		chosen_instruments = request.form.getlist('choose_instrument')
		for instrument_id in chosen_instruments:
			new_instrument_choice = InstrumentChoice(plan=plan, instrument_id=instrument_id)
			db.session.add(new_instrument_choice)	

		db.session.add(plan)
		db.session.commit()
		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))

	return render_template('main/plan.html', worksession=worksession, plan=plan, advisor=advisor)


@main.route('/worksession/<int:worksession_id>/new_plan', methods=['GET', 'POST'])
@login_required
def new_plan(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	if not current_user.role.see_all_worksessions and current_user not in worksession.allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	plan = Plan(worksession=worksession, date=datetime.today())

	if request.method == "POST":
		plan.description = request.form.get("plan_description")
		plan.conclusion = chosen_instruments = request.form.get("plan_motivation")
		#Store all checked instruments
		chosen_instruments = request.form.getlist('choose_instrument')
		for instrument_id in chosen_instruments:
			new_instrument_choice = InstrumentChoice(plan=plan, instrument_id=instrument_id)
			db.session.add(new_instrument_choice)	

		db.session.add(plan)
		db.session.commit()
		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))

	return render_template('main/plan.html', worksession=worksession, plan=plan, advisor=advisor)


@main.route('/worksession/delete_plan/<int:plan_id>')
@login_required
def delete_plan(plan_id):
	plan = Plan.query.get(plan_id)
	worksession = plan.worksession
	if not current_user.role.see_all_worksessions and current_user not in worksession.allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	db.session.delete(plan)
	db.session.commit()
	return redirect(url_for('main.show_worksession', worksession_id=worksession.id))


@main.route('/worksession/<int:worksession_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_worksession(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	form = EditWorksessionForm()
	form.choice_process.choices = [(process.id, process.name) for process in Process.query.order_by(Process.id)]

	if form.validate_on_submit():
		worksession.name = form.name.data
		worksession.project_number = form.project_number.data
		worksession.link_to_page = form.link_to_page.data
		worksession.participants = form.participants.data
		worksession.date = form.date.data
		worksession.process_id = form.choice_process.data
		worksession.description = form.description.data
		worksession.show_instruments = form.show_instruments.data
		worksession.mark_top_instruments = form.mark_top_instruments.data
		worksession.show_rest_instruments = form.show_rest_instruments.data
		worksession.show_tags = form.show_tags.data
		worksession.presenter_mode_zoom = form.presenter_mode_zoom.data
		worksession.presenter_mode_color_title = form.presenter_mode_color_title.data
		worksession.presenter_mode_text_color_title = form.presenter_mode_text_color_title.data
		worksession.presenter_mode_color_nav = form.presenter_mode_color_nav.data
		worksession.presenter_mode_text_color_nav = form.presenter_mode_text_color_nav.data
		worksession.presenter_mode_color_coll = form.presenter_mode_color_coll.data
		worksession.presenter_mode_text_color_coll = form.presenter_mode_text_color_coll.data
		worksession.presenter_mode_color_highlight = form.presenter_mode_color_highlight.data
		worksession.presenter_mode_text_color_highlight = form.presenter_mode_text_color_highlight.data
		worksession.presenter_mode_text_color_heading = form.presenter_mode_text_color_heading.data
		worksession.presenter_mode_text_color = form.presenter_mode_text_color.data
		worksession.presenter_mode_background_color1 = form.presenter_mode_background_color1.data
		worksession.presenter_mode_background_color2 = form.presenter_mode_background_color2.data
		worksession.archived = form.archived.data
		db.session.add(worksession)
		db.session.commit()
		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))
	elif request.method == 'GET':
		form.name.data = worksession.name
		form.link_to_page.data = worksession.link_to_page
		form.participants.data = worksession.participants
		form.date.data = worksession.date
		form.choice_process.data = worksession.process_id
		form.description.data = worksession.description
		form.show_instruments.data = worksession.show_instruments
		form.mark_top_instruments.data = worksession.mark_top_instruments 
		form.show_rest_instruments.data = worksession.show_rest_instruments
		form.show_tags.data = worksession.show_tags 
		form.presenter_mode_zoom.data = worksession.presenter_mode_zoom 
		form.presenter_mode_color_title.data = worksession.presenter_mode_color_title
		form.presenter_mode_text_color_title.data = worksession.presenter_mode_text_color_title
		form.presenter_mode_color_nav.data = worksession.presenter_mode_color_nav
		form.presenter_mode_text_color_nav.data = worksession.presenter_mode_text_color_nav
		form.presenter_mode_color_coll.data = worksession.presenter_mode_color_coll
		form.presenter_mode_text_color_coll.data = worksession.presenter_mode_text_color_coll
		form.presenter_mode_color_highlight.data = worksession.presenter_mode_color_highlight
		form.presenter_mode_text_color_highlight.data = worksession.presenter_mode_text_color_highlight
		form.presenter_mode_text_color_heading.data = worksession.presenter_mode_text_color_heading
		form.presenter_mode_text_color.data = worksession.presenter_mode_text_color
		form.presenter_mode_background_color1.data = worksession.presenter_mode_background_color1 
		form.presenter_mode_background_color2.data = worksession.presenter_mode_background_color2 
		form.archived.data = worksession.archived
		
	return render_template('main/edit_worksession.html', worksession=worksession, form=form)

@main.route('/worksession/<int:worksession_id>/archive')
@login_required
def archive_worksession(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	worksession.archived = True
	db.session.add(worksession)
	db.session.commit()
	return redirect(url_for('main.show_worksession', worksession_id=worksession.id))

@main.route('/worksession/<int:worksession_id>/delete')
@login_required
def delete_worksession(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	db.session.delete(worksession)
	db.session.commit()
	return redirect(url_for('main.index'))


@main.route('/worksession/<int:worksession_id>/present', methods=['GET', 'POST'])
@main.route('/worksession/<int:worksession_id>/present/<int:question_id>', methods=['GET', 'POST'])
@login_required
def present(worksession_id, question_id=None):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	if question_id is None:
		question = Question.query.filter_by(question_set=worksession.question_set).order_by(Question.order).first()
	else:	
		question = Question.query.get(question_id)
	answer = Answer.query.filter_by(worksession=worksession, question=question).first()
	
	if request.method == "POST":
		for answer in Answer.query.filter_by(worksession=worksession):
			# Delete all answers to replace them below.
			for selection in answer.selection:
				db.session.delete(selection)
			db.session.delete(answer)

		motivations = {}
		selected_options = []
		weights = {}
		for item, value in request.form.items():
			# De name-attribute van de textarea bevat het soort vraag (motivation, option), een :, en dan het vraagnummer of het optienummer.
			if 'motivation' in item:
				_, question_id = item.split(':', 1)
				motivations[int(question_id)] = value
			if 'option' in item:
				selected_options.append(int(value))
			if 'weight' in item:
				_, question_id = item.split(':', 1)
				weights[int(question_id)] = value

		for question in worksession.question_set.questions:
		# Alleen de vragen in de huidige question set
			if not question.is_category:
				new_answer = Answer(worksession=worksession, question=question, motivation=motivations.get(question.id), weight=weights.get(question.id))
				for option in question.options:
					if option.id in selected_options: 
						# De vraag zit in de huidige question set en moet aangevinkt worden.
						new_answer.selection.append(Selection(option=option))
				db.session.add(new_answer)
		db.session.commit()
		return redirect(url_for('main.present', worksession_id=worksession.id))
	return render_template('main/present.html', 
						worksession=worksession,
						current_question=question,
						advisor=advisor)


@main.route('/worksession/<int:worksession_id>/simultaneous', methods=['GET', 'POST'])
@login_required
def process_simultaneous(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	
	if request.method == "POST":
		for answer in Answer.query.filter_by(worksession=worksession):
			# Delete all answers to replace them below.
			for selection in answer.selection:
				db.session.delete(selection)
			db.session.delete(answer)

		motivations = {}
		selected_options = []
		weights = {}
		for item, value in request.form.items():
			# De name-attribute van de textarea bevat het soort vraag (motivation, option), een :, en dan het vraagnummer of het optienummer.
			if 'motivation' in item:
				_, question_id = item.split(':', 1)
				motivations[int(question_id)] = value
			if 'option' in item:
				selected_options.append(int(value))
			if 'weight' in item:
				_, question_id = item.split(':', 1)
				weights[int(question_id)] = value

		for question in worksession.question_set.questions:
		# Alleen de vragen in de huidige question set
			if not question.is_category:
				new_answer = Answer(worksession=worksession, question=question, motivation=motivations.get(question.id), weight=weights.get(question.id))
				for option in question.options:
					if option.id in selected_options: 
						# De vraag zit in de huidige question set en moet aangevinkt worden.
						new_answer.selection.append(Selection(option=option))
				db.session.add(new_answer)
		db.session.commit()
		return redirect(url_for('main.process_simultaneous', worksession_id=worksession.id))
	elif request.method == "GET":
		pass
	return render_template('main/simultaneous.html', worksession=worksession, advisor=advisor)

@main.route('/worksession/<int:worksession_id>/single', methods=['GET', 'POST'])
@main.route('/worksession/<int:worksession_id>/single/<int:question_id>', methods=['GET', 'POST'])
@login_required
def process_single(worksession_id, question_id=None):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	if question_id is None:
		# Without a question number, find the first question in order.
		question = Question.query.filter_by(question_set=worksession.question_set).order_by(Question.order).first()
	else:	
		question = Question.query.get(question_id)
	answer = Answer.query.filter_by(worksession=worksession, question=question).first()

	if request.method == "POST":
		if not question.is_category:
			if answer is not None:
				db.session.delete(answer)

			new_answer = Answer(worksession=worksession, question=question, motivation=request.form.get('motivation'), weight=request.form.get('weight'))
			for option in question.options:
				if str(option.id) in request.form.getlist('option'):
					# De vraag zit in de huidige question set en moet aangevinkt worden.
					new_answer.selection.append(Selection(option=option))
			db.session.add(new_answer)
			db.session.commit()

		next_question = None
		# Move to the next question. The next question is selected by taking all questiopns in the current set, taking only those with a order number higher than the current one, and sorting by order.
		for question in Question.query.filter_by(question_set=worksession.question_set).filter(Question.order > Question.query.get(question.id).order).order_by(Question.order): 
			if not worksession.is_question_hidden(question):
				next_question = question
				break
		if next_question is None:
			# If no question is found, move on the the conclusion page for this session.
			return redirect(url_for('main.conclusion', worksession_id=worksession.id))
		return redirect(url_for('main.process_single', worksession_id=worksession.id, question_id=next_question.id))
	elif request.method == "GET":
		pass
	return render_template('main/single.html', worksession=worksession, question=question, answer=answer, advisor=advisor)


@main.route('/worksession/<int:worksession_id>/case', methods=['GET', 'POST'])
@login_required
def case(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	form = EditCaseForm()

	if form.validate_on_submit():
		worksession.description = form.description.data
		worksession.effect = form.effect.data
		db.session.commit()
		
		# Redirect tot the first question in the set
		if worksession.process_id == 1:
			return redirect(url_for('main.process_simultaneous', worksession_id=worksession.id))
		elif worksession.process_id == 2:
			return redirect(url_for('main.process_single', worksession_id=worksession.id))
	elif request.method == "GET":
		form.description.data = worksession.description 
		form.effect.data = worksession.effect
	return render_template('/main/case.html', worksession=worksession, form=form)


@main.route('/worksession/<int:worksession_id>/conclusion', methods=['GET', 'POST'])
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
		#Store the conclusion with the new plan.
		plan.conclusion = chosen_instruments = request.form.get("motivation")
		#Erase previously selected instruments
		for instrument_choice in plan.instruments:
			db.session.delete(instrument_choice)
		#Store all checked instruments
		chosen_instruments = request.form.getlist('choose_instrument')
		for instrument_id in chosen_instruments:
			new_instrument_choice = InstrumentChoice(plan=plan,
											instrument_id=instrument_id)
			db.session.add(new_instrument_choice)	

		db.session.add(plan)
		db.session.commit()

		# Remind the user in 90 days to enter the final intervention plan
		send_system_message(
			subject = f'Welke interventies zijn uitgevoerd bij de casus {worksession.name}?',
			body = f'Laat weten welke interventies zijn uitgevoerd bij de casus {worksession.name}. Open de werksessie en voer een nieuw interventieplan in. Selecteer in het interventieplan de daadwerkelijk uitgevoerde interventies. Op basis van deze gegevens kunnen de selectietool en de instrumenten verder worden ontwikkeld.',
			deliver_after = date.today() + timedelta(90),
			recipient = current_user,
			sender = None
		)

		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))

	return render_template('/main/conclusion.html', 
						worksession=worksession, 
						advisor=advisor,
						plan=plan)


@main.route('/worksession/<int:worksession_id>/summary', methods=['GET', 'POST'])
@login_required
def worksession_summary(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	return render_template('/main/summary.html', worksession=worksession, advisor=advisor)


@main.route('/worksession/<int:worksession_id>/instrument/<int:instrument_id>')
@login_required
def show_instrument(worksession_id, instrument_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	instrument = Instrument.query.get(instrument_id)
	return render_template('main/instrument.html', worksession=worksession, instrument=instrument, advisor=advisor)


@main.route('/worksession/<int:worksession_id>/zoom/<int:change>')
@login_required
def zoom(worksession_id, change):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	if change == 1:
		worksession.presenter_mode_zoom = Decimal(1.00)
	elif change == 2:
		worksession.presenter_mode_zoom -= Decimal(0.05)
	elif change == 3:
		worksession.presenter_mode_zoom += Decimal(0.05)
	db.session.commit()
	return 'Zoom changed'


# @main.route('/worksession/<int:worksession_id>/share', methods=['GET', 'POST'])
# @login_required
# def share_worksession(worksession_id):
# 	"""There are two ways of inviting people to a worksession. The first is by creating an invitation link. Anyone who clicks that link 
# 	is granted access to a worksession. The second way is by directly adding users to a worksession. This can only be done bu admins, because
# 	only admins can see all users."""
# 	worksession = Worksession.query.get(worksession_id)
# 	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
# 		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

# 	to_be_hashed = f'{date.today()}{worksession.secret_key}'
# 	invitation_string = hashlib.sha1(to_be_hashed.encode('utf-8')).hexdigest()

# 	form = EditWorksessionAccessForm()
# 	form.user.choices = [(user.id, user.name) for user in User.query.order_by(User.name)]

# 	if form.validate_on_submit():
# 		for user_id in form.user.data:
# 			worksession.allowed_users.append(User.query.get(user_id))
# 		db.session.commit()
# 	elif request.method == "GET":
# 		pass
# 	return render_template('main/share_worksession.html', worksession=worksession, form=form, invitation_string=invitation_string)


@main.route('/worksession/<int:worksession_id>/reset_secret_key')
@login_required
def reset_secret_key(worksession_id):
	"""By resetting teh secret key, all invitations are invalidated."""
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	worksession.secret_key = generate_secret_key()
	db.session.commit()
	return redirect(url_for('main.show_worksession', worksession_id=worksession.id))


@main.route('/worksession/<int:worksession_id>/share_link/<string:invitation_string>')
@login_required
def share_link(worksession_id, invitation_string):
	"""Anyone who clicks the share link with an invitation string is granted access to the worksession. Invitation strings are hashed
	with the current date. This function generates hashes for the past seven days and checks for a match."""
	worksession = Worksession.query.get(worksession_id)

	for d in range(7):
		# Calculate hash for each day in the past week.
		date_to_check = date.today() - timedelta(days=d)
		to_be_hashed = f'{date_to_check}{worksession.secret_key}'
		if hashlib.sha1(to_be_hashed.encode('utf-8')).hexdigest() == invitation_string:
			worksession.allowed_users.append(current_user)
			db.session.commit()
			return redirect(url_for('main.show_worksession', worksession_id=worksession.id))
	return 'Uitnodiging ongeldig.'


@main.route('/worksession/<int:worksession_id>/stop_share/<int:user_id>')
@login_required
def stop_share(worksession_id, user_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	user = User.query.get(user_id)
	worksession.allowed_users.remove(user)
	db.session.commit()
	return redirect(url_for('main.show_worksession', worksession_id=worksession.id))