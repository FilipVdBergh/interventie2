from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, send_file, request
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.forms import LoginForm, NewSessionForm, EditSessionForm, EditCaseForm, EditConclusionForm, MarkdownPlaygroundForm, EditSessionAccessForm
from interventie2.models import User, Session, QuestionSet, Instrument, Option, Answer, Selection, Question, Process
from interventie2.models import db, generate_secret_key
from interventie2.classes import Advisor
from sqlalchemy.sql import func
from decimal import Decimal
import hashlib




main = Blueprint('main', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


@main.route('/')
@login_required
def index():
	sessions = Session.query.order_by(Session.name)
	return render_template('main/index.html', sessions=sessions)


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


@main.route('/new_session', methods=['GET', 'POST'])
@login_required
def new_session():
	form = NewSessionForm()
	form.question_set.choices = [(question_set.id, question_set.name) for question_set in QuestionSet.query.order_by(QuestionSet.name)]

	if form.validate_on_submit():
		session = Session()
		session.name = form.name.data
		session.link_to_page = form.link_to_page.data
		session.date = form.date.data
		session.participants = form.participants.data
		session.question_set_id = form.question_set.data
		session.creator = current_user
		session.show_instruments = QuestionSet.query.get(session.question_set_id).default_instruments_visible
		session.show_tags =  QuestionSet.query.get(session.question_set_id).default_instruments_visible
		session.process_id = QuestionSet.query.get(session.question_set_id).default_process_id
		session.presenter_mode_zoom = 1.25
		session.presenter_mode_color_title = '#FFFFFF'
		session.presenter_mode_text_color_title ='#000061'
		session.presenter_mode_color_nav = '#091e31'
		session.presenter_mode_text_color_nav ='#d7d7d7'
		session.presenter_mode_text_color_heading = '#000061'
		session.presenter_mode_text_color = '#000000'
		session.presenter_mode_color_coll = '#EEEEEE'
		session.presenter_mode_text_color_coll ='#000000'
		session.presenter_mode_color_highlight = '#65C7FF'
		session.presenter_mode_text_color_highlight ='#000000'
		session.presenter_mode_background_color1 = '#FFFFFF'
		session.presenter_mode_background_color2 = '#F7F7F7'
		session.allowed_users.append(current_user)
		session.archived = False
		db.session.add(session)
		db.session.commit()
		return redirect(url_for('main.show_session', session_id=session.id))
	elif request.method == 'GET':
		pass
	return render_template('main/new_session.html', form=form)


@main.route('/clone_session/<int:session_id>', methods=['GET', 'POST'])
@login_required
def clone_session(session_id):
	parent_session = Session.query.get(session_id)

	if request.method == "POST":
		session = Session()
		session.name = parent_session.name
		session.participants = parent_session.participants
		session.date = parent_session.date
		session.description = parent_session.description
		session.effect = parent_session.effect
		session.conclusion == parent_session.conclusion
		session.question_set_id = parent_session.question_set_id
		session.creator = current_user
		session.show_instruments = parent_session.show_instruments
		session.show_tags =parent_session.show_tags
		session.process_id = parent_session.process_id
		session.presenter_mode_zoom = parent_session.presenter_mode_zoom
		session.presenter_mode_color_title = parent_session.presenter_mode_color_title
		session.presenter_mode_text_color_title = parent_session.presenter_mode_text_color_title
		session.presenter_mode_color_nav = parent_session.presenter_mode_color_nav
		session.presenter_mode_text_color_nav = parent_session.presenter_mode_text_color_nav
		session.presenter_mode_text_color_heading = parent_session.presenter_mode_text_color_heading 
		session.presenter_mode_text_color = parent_session.presenter_mode_text_color
		session.presenter_mode_color_coll = parent_session.presenter_mode_color_coll
		session.presenter_mode_text_color_coll = parent_session.presenter_mode_text_color_coll
		session.presenter_mode_color_highlight = parent_session.presenter_mode_color_highlight
		session.presenter_mode_text_color_highlight =parent_session.presenter_mode_text_color_highlight
		session.presenter_mode_background_color1 = parent_session.presenter_mode_background_color1
		session.presenter_mode_background_color2 = parent_session.presenter_mode_background_color2
		session.allowed_users.append(parent_session.creator)
		session.archived = False
		session.parent = Session.query.get(session_id)
		session.child_description = request.form.getlist('child_description')
		
		db.session.add(session)
		db.session.commit()
		return redirect(url_for('main.show_session', session_id=session.id))
	elif request.method == "GET":
		pass
	return render_template('main/clone_session.html', session=parent_session)


@main.route('/session/<int:session_id>')
@login_required
def show_session(session_id):
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	return render_template('main/session.html', session=Session.query.get(session_id), sessions=Session.query.order_by(Session.name))


@main.route('/session/<int:session_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_session(session_id):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	form = EditSessionForm()
	form.choice_process.choices = [(process.id, process.name) for process in Process.query.order_by(Process.id)]

	if form.validate_on_submit():
		session.name = form.name.data
		session.link_to_page = form.link_to_page.data
		session.participants = form.participants.data
		session.date = form.date.data
		session.process_id = form.choice_process.data
		session.description = form.description.data
		session.show_instruments = form.show_instruments.data
		session.mark_top_instruments = form.mark_top_instruments.data
		session.show_rest_instruments = form.show_rest_instruments.data
		session.show_tags = form.show_tags.data
		session.presenter_mode_zoom = form.presenter_mode_zoom.data
		session.presenter_mode_color_title = form.presenter_mode_color_title.data
		session.presenter_mode_text_color_title = form.presenter_mode_text_color_title.data
		session.presenter_mode_color_nav = form.presenter_mode_color_nav.data
		session.presenter_mode_text_color_nav = form.presenter_mode_text_color_nav.data
		session.presenter_mode_color_coll = form.presenter_mode_color_coll.data
		session.presenter_mode_text_color_coll = form.presenter_mode_text_color_coll.data
		session.presenter_mode_color_highlight = form.presenter_mode_color_highlight.data
		session.presenter_mode_text_color_highlight = form.presenter_mode_text_color_highlight.data
		session.presenter_mode_text_color_heading = form.presenter_mode_text_color_heading.data
		session.presenter_mode_text_color = form.presenter_mode_text_color.data
		session.presenter_mode_background_color1 = form.presenter_mode_background_color1.data
		session.presenter_mode_background_color2 = form.presenter_mode_background_color2.data
		session.archived = form.archived.data
		db.session.add(session)
		db.session.commit()
		return redirect(url_for('main.show_session', session_id=session.id))
	elif request.method == 'GET':
		form.name.data = session.name
		form.link_to_page.data = session.link_to_page
		form.participants.data = session.participants
		form.date.data = session.date
		form.choice_process.data = session.process_id
		form.description.data = session.description
		form.show_instruments.data = session.show_instruments
		form.mark_top_instruments.data = session.mark_top_instruments 
		form.show_rest_instruments.data = session.show_rest_instruments
		form.show_tags.data = session.show_tags 
		form.presenter_mode_zoom.data = session.presenter_mode_zoom 
		form.presenter_mode_color_title.data = session.presenter_mode_color_title
		form.presenter_mode_text_color_title.data = session.presenter_mode_text_color_title
		form.presenter_mode_color_nav.data = session.presenter_mode_color_nav
		form.presenter_mode_text_color_nav.data = session.presenter_mode_text_color_nav
		form.presenter_mode_color_coll.data = session.presenter_mode_color_coll
		form.presenter_mode_text_color_coll.data = session.presenter_mode_text_color_coll
		form.presenter_mode_color_highlight.data = session.presenter_mode_color_highlight
		form.presenter_mode_text_color_highlight.data = session.presenter_mode_text_color_highlight
		form.presenter_mode_text_color_heading.data = session.presenter_mode_text_color_heading
		form.presenter_mode_text_color.data = session.presenter_mode_text_color
		form.presenter_mode_background_color1.data = session.presenter_mode_background_color1 
		form.presenter_mode_background_color2.data = session.presenter_mode_background_color2 
		form.archived.data = session.archived
		
	return render_template('main/edit_session.html', session=session, form=form)


@main.route('/session/<int:session_id>/delete')
@login_required
def delete_session(session_id):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	db.session.delete(session)
	db.session.commit()
	return redirect(url_for('main.index'))

@main.route('/session/<int:session_id>/simultaneous', methods=['GET', 'POST'])
@login_required
def process_simultaneous(session_id):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	advisor = Advisor(session=session, instruments=Instrument.query.all())
	
	if request.method == "POST":
		for answer in Answer.query.filter_by(session=session):
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

		for question in session.question_set.questions:
		# Alleen de vragen in de huidige question set
			if not question.is_category:
				new_answer = Answer(session=session, question=question, motivation=motivations.get(question.id), weight=weights.get(question.id))
				for option in question.options:
					if option.id in selected_options: 
						# De vraag zit in de huidige question set en moet aangevinkt worden.
						new_answer.selection.append(Selection(option=option))
				db.session.add(new_answer)
		db.session.commit()
		return redirect(url_for('main.process_simultaneous', session_id=session.id))
	elif request.method == "GET":
		pass
	return render_template('main/simultaneous.html', session=session, advisor=advisor)

@main.route('/session/<int:session_id>/single', methods=['GET', 'POST'])
@main.route('/session/<int:session_id>/single/<int:question_id>', methods=['GET', 'POST'])
@login_required
def process_single(session_id, question_id=None):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	advisor = Advisor(session=session, instruments=Instrument.query.all())
	if question_id is None:
		# Without a question number, find the first question in order.
		question = Question.query.filter_by(question_set=session.question_set).order_by(Question.order).first()
	else:	
		question = Question.query.get(question_id)

	answer = Answer.query.filter_by(session=session, question=question).first()
	
	if request.method == "POST":
		if not question.is_category:
			if answer is not None:
				# Delete all answers to replace them below.
				for selection in answer.selection:
					db.session.delete(selection)
				db.session.delete(answer)

			new_answer = Answer(session=session, question=question, motivation=request.form.get('motivation'), weight=request.form.get('weight'))
			for option in question.options:
				if str(option.id) in request.form.getlist('option'):
					# De vraag zit in de huidige question set en moet aangevinkt worden.
					new_answer.selection.append(Selection(option=option))
			db.session.add(new_answer)
			db.session.commit()
		# Return the next question in the set.
		next_question = Question.query.filter_by(question_set=session.question_set).filter(Question.order > Question.query.get(question.id).order).order_by(Question.order).first()
		if next_question is None:
			return redirect(url_for('main.conclusion', session_id=session.id))
		else:
			return redirect(url_for('main.process_single', session_id=session.id, question_id=next_question.id))
	elif request.method == "GET":
		pass
	return render_template('main/single.html', session=session, question=question, answer=answer, advisor=advisor)


@main.route('/session/<int:session_id>/case', methods=['GET', 'POST'])
@login_required
def case(session_id):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	form = EditCaseForm()

	if form.validate_on_submit():
		session.description = form.description.data
		session.effect = form.effect.data
		db.session.commit()
		
		# Redirect tot the first question in the set
		if session.process_id == 1:
			return redirect(url_for('main.process_simultaneous', session_id=session.id))
		elif session.process_id == 2:
			return redirect(url_for('main.process_single', session_id=session.id))
	elif request.method == "GET":
		form.description.data = session.description 
		form.effect.data = session.effect
	return render_template('/main/case.html', session=session, form=form)


@main.route('/session/<int:session_id>/conclusion', methods=['GET', 'POST'])
@login_required
def conclusion(session_id):
	session = Session.query.get(session_id)
	advisor = Advisor(session=session, instruments=Instrument.query.all())
	
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	form = EditConclusionForm()

	if form.validate_on_submit():
		session.conclusion = form.conclusion.data
		db.session.commit()
		return redirect(url_for('export.index', session_id=session.id))
	elif request.method == "GET":
		form.conclusion.data = session.conclusion
	return render_template('/main/conclusion.html', session=session, form=form, advisor=advisor)


@main.route('/session/<int:session_id>/summary', methods=['GET', 'POST'])
@login_required
def session_summary(session_id):
	session = Session.query.get(session_id)
	advisor = Advisor(session=session, instruments=Instrument.query.all())
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	return render_template('/main/summary.html', session=session, advisor=advisor)


@main.route('/session/<int:session_id>/instrument/<int:instrument_id>')
@login_required
def show_instrument(session_id, instrument_id):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	advisor = Advisor(session=session, instruments=Instrument.query.all())
	instrument = Instrument.query.get(instrument_id)
	return render_template('main/instrument.html', session=session, instrument=instrument, advisor=advisor)


@main.route('/session/<int:session_id>/zoom/<int:change>')
@login_required
def zoom(session_id, change):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	if change == 1:
		session.presenter_mode_zoom = Decimal(1.00)
	elif change == 2:
		session.presenter_mode_zoom -= Decimal(0.05)
	elif change == 3:
		session.presenter_mode_zoom += Decimal(0.05)
	db.session.commit()
	return 'Zoom changed'


@main.route('/session/<int:session_id>/share', methods=['GET', 'POST'])
@login_required
def share_session(session_id):
	"""There are two ways of inviting people to a session. The first is by creating an invitation link. Anyone who clicks that link 
	is granted access to a session. The second way is by directly adding users to a session. This can only be done bu admins, because
	only admins can see all users."""
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	to_be_hashed = f'{date.today()}{session.secret_key}'
	invitation_string = hashlib.sha1(to_be_hashed.encode('utf-8')).hexdigest()

	form = EditSessionAccessForm()
	form.user.choices = [(user.id, user.name) for user in User.query.order_by(User.name)]

	if form.validate_on_submit():
		for user_id in form.user.data:
			session.allowed_users.append(User.query.get(user_id))
		db.session.commit()
	elif request.method == "GET":
		pass
	return render_template('main/share_session.html', session=session, form=form, invitation_string=invitation_string)


@main.route('/session/<int:session_id>/reset_secret_key')
@login_required
def reset_secret_key(session_id):
	"""By resetting teh secret key, all invitations are invalidated."""
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	session.secret_key = generate_secret_key()
	db.session.commit()
	return redirect(url_for('main.show_session', session_id=session.id))


@main.route('/session/<int:session_id>/share_link/<string:invitation_string>')
@login_required
def share_link(session_id, invitation_string):
	"""Anyone who clicks the share link with an invitation string is granted access to the session. Invitation strings are hashed
	with the current date. This function generates hashes for the past seven days and checks for a match."""
	session = Session.query.get(session_id)

	for d in range(7):
		# Calculate hash for each day in the past week.
		date_to_check = date.today() - timedelta(days=d)
		to_be_hashed = f'{date_to_check}{session.secret_key}'
		if hashlib.sha1(to_be_hashed.encode('utf-8')).hexdigest() == invitation_string:
			session.allowed_users.append(current_user)
			db.session.commit()
			return redirect(url_for('main.show_session', session_id=session.id))
	return 'Uitnodiging ongeldig.'


@main.route('/session/<int:session_id>/stop_share/<int:user_id>')
@login_required
def stop_share(session_id, user_id):
	session = Session.query.get(session_id)
	if not current_user.role.see_all_sessions and current_user not in Session.query.get(session_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	user = User.query.get(user_id)
	session.allowed_users.remove(user)
	db.session.commit()
	return redirect(url_for('main.share_session', session_id=session.id))


def debug_answers(session_id):
	session = Session.query.get(session_id)
	print (f'{session.name}'.upper())
	for answer in session.answers:
		print (f'{answer.question.name}:')
		for selection in answer.selection:
			print(f'- Option: {selection.option.name}')
		print (f'- Motivation: {answer.motivation}')
	print('All options in question set:')
	for question in session.question_set.questions:
		for option in question.options:
			print(f'- {option.name} {session.is_option_selected(option)}')