from datetime import date, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, send_file, request, flash, current_app, make_response
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.forms import LoginForm, EditWorksessionForm, EditCaseForm, MarkdownPlaygroundForm, EditWorksessionAccessForm
from interventie2.models import User, Role, Worksession, QuestionSet, Instrument, Answer, Selection, Question, InstrumentChoice, Plan, Votes
from interventie2.models import db, generate_secret_key
from interventie2.classes import Advisor
from sqlalchemy.sql import func, or_
from decimal import Decimal
from datetime import datetime
# from interventie2.admin.routes import send_system_message
import hashlib
from urllib.parse import urlsplit
# For downloading multiple exports
import os
from glob import glob
from shutil import make_archive, rmtree
from interventie2.export.routes import export_worksession_to_word


main = Blueprint('main', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')




@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
	worksessions = Worksession.query.filter(Worksession.archived==False).order_by(Worksession.date)

	return render_template('main/index.html', 
						worksessions=worksessions,
						today=datetime.today().date())


@main.route('/worksessions', methods=['GET', 'POST'])
@login_required
def worksessions():
	worksessions = Worksession.query.order_by(Worksession.date)
	question_sets =  QuestionSet.query.order_by(QuestionSet.name)

	return render_template('main/worksessions.html', 
						worksessions=worksessions,
						question_sets=question_sets,)


@main.route('/login', methods=['GET', 'POST'])
def login():
	# Redirect if already logged in
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(name=form.name.data).first()
		if user is None or not user.check_password(form.password.data):
			flash("Gebruikersnaam of wachtwoord onjuist", "login_error")
			return redirect(url_for('main.login'))
		if not user.active:
			flash("Inloggen voor deze gebruiker niet toegestaan", "login_error")
			return redirect(url_for('main.login'))
		login_user(user)
		user.last_seen = func.now()
		db.session.commit()

		next_page = request.args.get('next')
		if not next_page or urlsplit(next_page).netloc != '':
			next_page = url_for('main.index')
		return redirect(next_page)

	return render_template('main/login.html', form=form)


@main.route('/logout')
@login_required
def logout():
	db.session.add(current_user) 
	db.session.commit()
	logout_user()
	return redirect(url_for('main.index'))


@main.route('/worksessions/ws_upcoming')
@login_required
def ws_upcoming():	
	"""This view returns all worksessions that are active and that are owned by the user."""
	worksessions_ll = Worksession.query.filter(Worksession.archived==False, Worksession.date >= datetime.today().date()).order_by(Worksession.date).all()
	worksessions = []
	for ws in worksessions_ll:
		if ws.creator == current_user:
			worksessions.append(ws)
		elif current_user in ws.allowed_users:
			worksessions.append(ws)
	
	return render_template('main/ws_upcoming_cards.html', worksessions=worksessions)


@main.route('/worksessions/ws_owned')
@login_required
def ws_owned():	
	"""This view returns all worksessions that are active and that are owned by the user."""
	worksessions = Worksession.query.filter(Worksession.archived==False, Worksession.creator==current_user).order_by(Worksession.date).all()

	if len(worksessions): 
		return render_template('main/ws_owned_cards.html', worksessions=worksessions)

	return ""


@main.route('/worksessions/ws_new')
@login_required
def ws_new():	
	"""This view returns cards for all question_sets"""
	question_sets = QuestionSet.query.all()

	if len(question_sets):
		return render_template('main/ws_new_cards.html', question_sets=question_sets)
	
	return ""


@main.route('/worksessions/ws_shared')
@login_required
def ws_shared():	
	"""This view returns all worksessions that are active and that are shared with the user."""
	worksessions = current_user.allowed_worksessions
	
	if len(worksessions): 
		return render_template('main/ws_shared_cards.html', worksessions=worksessions)
	
	return ""


@main.route('/worksessions/ws_all')
@login_required
def ws_all():	
	"""This view returns alle questions sets that the user is allowed to see."""
	worksessions = current_user.list_allowed_worksessions()
	
	if len(worksessions): 
		return render_template('main/ws_all_table.html', worksessions=worksessions)
	
	return ""


@main.route('/worksessions/edit/archive', methods=['POST'])
@login_required
def edit_archive():
	worksessions_to_edit = []

	for item, value in request.form.items():
		# Create list of worksessions to be affected:
		if "ws:::" in item:
			if current_user.role.see_all_worksessions or current_user  in Worksession.query.get(value).allowed_users:
				# Only allow changes to the session if the user has the proper rights. This should be redundant for normal use through the interface.
				worksessions_to_edit.append(Worksession.query.get(value))
	for worksession in worksessions_to_edit:
		worksession.archived=True
	
	worksessions = current_user.list_allowed_worksessions()
	return render_template('main/ws_all_table.html', worksessions=worksessions)


@main.route('/worksessions/edit/activate', methods=['POST'])
@login_required
def edit_activate():
	worksessions_to_edit = []

	for item, value in request.form.items():
		print(f'{item}: {value}')
		# Create list of worksessions to be affected:
		if "ws:::" in item:
			if current_user.role.see_all_worksessions or current_user  in Worksession.query.get(value).allowed_users:
				# Only allow changes to the session if the user has the proper rights. This should be redundant for normal use through the interface.
				worksessions_to_edit.append(Worksession.query.get(value))
	for worksession in worksessions_to_edit:
		worksession.archived=False
	
	worksessions = current_user.list_allowed_worksessions()
	return render_template('main/ws_all_table.html', worksessions=worksessions)


@main.route('/worksessions/edit/export', methods=['POST'])
@login_required
def edit_export():
	worksessions_to_edit = []

	for item, value in request.form.items():
		# Create list of worksessions to be affected:
		if "ws:::" in item:
			if current_user.role.see_all_worksessions or current_user  in Worksession.query.get(value).allowed_users:
				# Only allow changes to the session if the user has the proper rights. This should be redundant for normal use through the interface.
				worksessions_to_edit.append(Worksession.query.get(value))

	# Housekeeping for all the locations and filenames:
	exports_location = os.path.join(current_app.static_folder, 'export', str(current_user.id))
	archive_filename = os.path.join(current_app.static_folder, 'export', f'{current_user.id}')
	if not os.path.exists(exports_location):
		os.makedirs(exports_location)

	# Creating all the files:
	for worksession in worksessions_to_edit:
		export_worksession_to_word(worksession, location=exports_location)

	# Making the archive and cleaning up:
	make_archive(archive_filename, 'zip', root_dir=exports_location, base_dir='./')
	rmtree(exports_location, ignore_errors=True)

	return render_template('main/export_archive_ready.html')

@main.route('/worksessions/edit/export_archive_ready', methods=['GET'])
@login_required
def edit_export_archive_ready():
	# Exported worksessions are always saved to an archive named after the user id. Furthermore, users can only every download
	# archives named after their user id. This should ensure that it is never possible to download sessions you have no access to.
	archive_filename = os.path.join(current_app.static_folder, 'export', f'{current_user.id}.zip')
	return send_file (archive_filename, as_attachment=True, download_name='exported_worksessions.zip')
	

@main.route('/worksessions/edit/delete', methods=['POST'])
@login_required
def edit_delete():
	worksessions_to_edit = []
	CONFIRM = False # Deleting multiple worksessiopns require that the user not only clicks the button, but also checks a box.

	for item, value in request.form.items():
		# Deleting sessions requires an additional checkbox to be checked.
		if "confirm_delete" in item:
			CONFIRM = True
		# Create list of worksessions to be affected:
		if "ws:::" in item:
			if current_user.role.see_all_worksessions or current_user  in Worksession.query.get(value).allowed_users:
				# Only allow changes to the session if the user has the proper rights. This should be redundant for normal use through the interface.
				worksessions_to_edit.append(Worksession.query.get(value))

	if CONFIRM:
		for worksession in worksessions_to_edit:
			db.session.delete(worksession)
		db.session.commit()
	
	worksessions = current_user.list_allowed_worksessions()
	return render_template('main/ws_all_table.html', worksessions=worksessions)


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


@main.route('/new_worksession/question_set/<int:question_set_id>', methods=['GET', 'POST'])
# @main.route('/new_worksession', methods=['GET', 'POST'])
@login_required
def new_worksession(question_set_id=None):
	"""New worksession based on a question set."""
	form = EditWorksessionForm()
	# form.question_set.choices = [(question_set.id, question_set.name) for question_set in QuestionSet.query.order_by(QuestionSet.name)]

	# if question_set_id is not None:
	# 	form.question_set.data = question_set_id
	# 	form.question_set.hidden = True

	if form.validate_on_submit():
		worksession = Worksession()
		worksession.name = form.name.data
		worksession.project_number = form.project_number.data
		worksession.link_to_page = form.link_to_page.data
		worksession.date = datetime.combine(form.date.data, datetime.min.time())
		worksession.date_modified = datetime.today()
		worksession.participants = form.participants.data
		worksession.description = form.description.data
		worksession.effect = form.effect.data
		# worksession.question_set_id = form.question_set.data
		worksession.creator = current_user
		worksession.show_instruments = form.show_instruments.data
		worksession.show_rest_instruments = form.show_rest_instruments.data
		worksession.mark_top_instruments = form.mark_top_instruments.data
		worksession.show_tags = form.show_tags.data
		worksession.enable_voting = form.enable_voting.data
		worksession.voting_key = generate_secret_key(6)
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

		worksession.question_set = QuestionSet.query.get(question_set_id)
		
		db.session.add(worksession)
		db.session.commit()
			
		return redirect(url_for('main.show_worksession', worksession_id=worksession.id))
	elif request.method == 'GET':
		form.show_instruments.data = QuestionSet.query.get(question_set_id).default_instruments_visible
		form.show_tags.data =  QuestionSet.query.get(question_set_id).default_tags_visible
		# The default session date is 14 days after creationg a new session.
		form.date.data = datetime.today()+ timedelta(14)
	return render_template('main/edit_worksession.html', form=form)



@main.route('/new_worksession/base_session/<int:base_session_id>/question_set/<int:question_set_id>')
@login_required
def new_worksession_from_base(question_set_id, base_session_id=None):
	"""New worksession based on a previous session."""
	worksession = Worksession()

	if base_session_id is not None:
		worksession_base = Worksession.query.get(base_session_id)
		worksession.name = worksession_base.name
		worksession.description = worksession_base.description
		worksession.effect = worksession_base.effect
		worksession.project_number = worksession_base.project_number
		worksession.link_to_page = worksession_base.link_to_page
	worksession.date = datetime.today()
	worksession.participants = ''
	worksession.question_set_id = question_set_id
	worksession.creator = current_user
	worksession.show_instruments = QuestionSet.query.get(question_set_id).default_instruments_visible
	worksession.show_tags =  QuestionSet.query.get(question_set_id).default_tags_visible
	worksession.process_id = QuestionSet.query.get(question_set_id).default_process_id
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
		
	return redirect(url_for('main.edit_worksession', worksession_id=worksession.id))


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

	return render_template('main/worksession.html', 
						worksession=worksession, 
						advisor=advisor,
						form=form,
						invitation_string=invitation_string)

@main.route('/worksession/<int:worksession_id>/questions_tags')
@login_required
def ws_questions_tags(worksession_id):
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	worksession = Worksession.query.get(worksession_id)
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())

	return render_template('main/ws_questions_tags.html', worksession=worksession, advisor=advisor)


@main.route('/worksession/<int:worksession_id>/show_plans')
@login_required
def ws_show_plans(worksession_id):
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	worksession = Worksession.query.get(worksession_id)

	return render_template('main/ws_show_plans.html', worksession=worksession)


@main.route('/worksession/<int:worksession_id>/followup')
@login_required
def ws_followup(worksession_id):
	"""Create a follow-up session with the same information."""
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	worksession = Worksession.query.get(worksession_id)
	question_sets =  QuestionSet.query.order_by(QuestionSet.name)

	return render_template('main/ws_followup_cards.html', worksession=worksession, question_sets=question_sets)


@main.route('/worksession/<int:worksession_id>/related_projects')
@login_required
def ws_projectnumber(worksession_id):
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	worksession = Worksession.query.get(worksession_id)
	related_worksessions = Worksession.query.filter_by(project_number=worksession.project_number).order_by(Worksession.name)

	return render_template('main/ws_projectnumber_cards.html', related_worksessions=related_worksessions)


@main.route('/worksession/<int:worksession_id>/plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def show_plan(worksession_id, plan_id):
	plan = Plan.query.get(plan_id)
	worksession = plan.worksession
	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	if not current_user.role.see_all_worksessions and current_user not in worksession.allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	return render_template('main/plan.html', worksession=worksession, plan=plan, advisor=advisor)

@main.route('/worksession/<int:worksession_id>/plan/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(worksession_id, plan_id):
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
		return redirect(url_for('main.show_plan', worksession_id=worksession.id, plan_id=plan.id))

	return render_template('main/edit_plan.html', worksession=worksession, plan=plan, advisor=advisor)


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

	return render_template('main/edit_plan.html', worksession=worksession, plan=plan, advisor=advisor)


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

	if form.validate_on_submit():
		worksession.name = form.name.data
		worksession.project_number = form.project_number.data
		worksession.link_to_page = form.link_to_page.data
		worksession.participants = form.participants.data
		worksession.date = datetime.combine(form.date.data, datetime.min.time())
		# worksession.process_id = form.choice_process.data
		worksession.description = form.description.data
		worksession.effect = form.effect.data
		worksession.show_instruments = form.show_instruments.data
		worksession.mark_top_instruments = form.mark_top_instruments.data
		worksession.show_rest_instruments = form.show_rest_instruments.data
		worksession.show_tags = form.show_tags.data
		worksession.enable_voting = form.enable_voting.data
		worksession.voting_key = generate_secret_key(6)
		worksession.presenter_mode_zoom = 1.00
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
		form.project_number.data = worksession.project_number
		form.link_to_page.data = worksession.link_to_page
		form.participants.data = worksession.participants
		form.date.data = worksession.date
		# form.choice_process.data = worksession.process_id
		form.description.data = worksession.description
		form.effect.data = worksession.effect
		form.show_instruments.data = worksession.show_instruments
		form.mark_top_instruments.data = worksession.mark_top_instruments 
		form.show_rest_instruments.data = worksession.show_rest_instruments
		form.show_tags.data = worksession.show_tags 
		form.enable_voting.data = worksession.enable_voting
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


@main.route('/worksession/<int:worksession_id>/archive/<int:archive>')
@main.route('/worksession/<int:worksession_id>/archive')
@login_required
def archive_worksession(worksession_id, archive=1):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	worksession.archived = (archive==1)
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


@main.route('/worksession/<int:worksession_id>/instrument/<int:instrument_id>')
@login_required
def show_instrument(worksession_id, instrument_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')

	advisor = Advisor(worksession=worksession, instruments=Instrument.query.all())
	instrument = Instrument.query.get(instrument_id)
	return render_template('main/instrument.html', worksession=worksession, instrument=instrument, advisor=advisor)


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



@main.route('/worksession/<int:worksession_id>/reset_voting_key')
@login_required
def reset_voting_key(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	worksession.voting_key = generate_secret_key(6)
	db.session.commit()
	return ""


@main.route('/worksession/<int:worksession_id>/erase_votes')
@login_required
def erase_votes(worksession_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users:
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze sessie te zien.')
	
	worksession.voting_key = generate_secret_key(6)
	
	votes = Votes.query.filter_by(worksession=worksession).all()
	for vote in votes:
		db.session.delete(vote)
	db.session.commit()

	return redirect(url_for('main.show_worksession', worksession_id=worksession.id))



@main.route('/worksession/<int:worksession_id>/reset_secret_key')
@login_required
def reset_secret_key(worksession_id):
	"""By resetting the secret key, all invitations are invalidated."""
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


@main.route('/worksession/<int:worksession_id>/make_owner/<int:user_id>')
@login_required
def make_owner(worksession_id, user_id):
	worksession = Worksession.query.get(worksession_id)
	if not current_user.role.see_all_worksessions and current_user not in Worksession.query.get(worksession_id).allowed_users: 
		return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om de eigenaar te veranderen.')

	user = User.query.get(user_id)
	worksession.creator = user
	db.session.commit()
	return redirect(url_for('main.show_worksession', worksession_id=worksession.id))