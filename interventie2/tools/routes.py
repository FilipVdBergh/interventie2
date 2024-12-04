import os
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from interventie2.models import User
from interventie2.models import db, QuestionSet, Process, User, Question, Answer, Option, Tag, Worksession, InstrumentTagAssignment
from interventie2.forms import QuestionSetForm, AddQuestionForm, QuestionForm, OptionForm, AddTagToQuestionSet, AddRequiredTagToQuestionForm, TagForm
from sqlalchemy.sql import func
import simplejson as json

tools = Blueprint('tools', __name__,
                 template_folder='templates',
                 static_folder='static',
                 static_url_path='assets')


@tools.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question_sets = QuestionSet.query.order_by()
    form = TagForm()
    tags = Tag.query.order_by(Tag.name)
    if form.validate_on_submit():
        if Tag.query.filter_by(Tag.name==form.name.data).first():
            return render_template('error/index.html', title='Tag bestaat al', message='Er bestaat al een tag met deze naam.')

        tag = Tag(name = form.name.data)
        db.session.add(tag)
        db.session.commit()
        return redirect(url_for('tools.tags'))
    elif request.method == 'GET':
        pass
    return render_template('tools/index.html', question_sets=question_sets, edit_catalog_allowed=current_user.role.edit_catalog, tags=tags, form=form)  


@tools.route('list_worksessions/<int:question_set_id>', methods=['GET', 'POST'])
@login_required
def list_worksessions(question_set_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    
    question_set = QuestionSet.query.get(question_set_id)
    return render_template('tools/list_worksessions_based_on_tool.html', question_set=question_set)


@tools.route('/edit_question_set/<int:question_set_id>', methods=['GET', 'POST'])
@tools.route('/add_question_set', methods=['GET', 'POST'])
@login_required
def edit_question_set(question_set_id=None):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')

    form=QuestionSetForm()
    form.default_process.choices = [(process.id, process.name) for process in Process.query.order_by(Process.id)]
    form.owner.choices = []
    for user in User.query.order_by(User.name):
        if user.role.edit_questionnaire:
            form.owner.choices.append([user.id, user.name])

    if question_set_id is not None: # Bestaande tool bewerken
        question_set = QuestionSet.query.get(question_set_id)
    else:              # Nieuwe tool maken
        question_set = QuestionSet(default_process=Process.query.get(1), default_instruments_visible=True, default_tags_visible=True)
        if current_user.role.edit_questionnaire: # Dit is eigenlijk per definitie zo, anders kan je nooit op deze pagina zijn.]
            form.owner.data = current_user.id
        form.submit.label.text = 'Selectietool toevoegen'

    if form.validate_on_submit():
        question_set.name = form.name.data
        question_set.description = form.description.data
        question_set.owner_id = form.owner.data
        question_set.default_process = Process.query.get(form.default_process.data)
        question_set.default_instruments_visible = form.default_instruments_visible.data
        question_set.default_tags_visible = form.default_tags_visible.data
        question_set.default_allow_weights = form.default_allow_weights.data
        question_set.color = form.color.data
        question_set.text_color = form.text_color.data
        if question_set_id is None: # Nieuwe tool
            db.session.add(question_set)
        db.session.commit()
        return redirect(url_for('tools.view_question_set', question_set_id=question_set.id))
    elif request.method == 'GET' and question_set_id is not None:
        form.name.data = question_set.name
        form.description.data = question_set.description
        form.owner.data = question_set.owner_id 
        form.default_process.data = question_set.default_process_id
        form.default_instruments_visible.data = question_set.default_instruments_visible
        form.default_tags_visible.data = question_set.default_tags_visible
        form.default_allow_weights.data = question_set.default_allow_weights
        form.color.data = question_set.color
        form.text_color.data = question_set.text_color
    return render_template('tools/question_set_properties.html', form=form, question_set=question_set)


@tools.route('/import_question_set', methods=['GET', 'POST'])
@login_required
def import_question_set():
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te importeren.')
    
    if request.method == "POST":
        uploaded_file = request.files['file']

        if uploaded_file.filename != '':
            question_set_file = os.path.join(current_app.static_folder, 'import', uploaded_file.filename)
            uploaded_file.save(question_set_file)

            f = open(question_set_file)
            question_set_json = json.load(f)

            # Check if the filetype and version match
            if not(question_set_json['filetype'] == 'question_set'):
                return render_template('error/index.html', title='Verkeerde bestandstype', message=f"Het bestand beschrijft geen tool (filetype: {question_json['filetype']}). Importeren is niet mogelijk.")
                
            if not(question_set_json['filetype_version'] == current_app.config['FILETYPE_VERSION']):
                return render_template('error/index.html', title='Verkeerde indelingsversie', message=f"Het bestand heeft indelingsversie {question_json['filetype_version']}, en de applicatie verwacht indelingsversie {current_app.config['FILETYPE_VERSION']}. Importeren is niet mogelijk.")

            # Rename tool in case of a duplicate tool name in the database:
            imported_name = question_set_json['name']
            if QuestionSet.query.filter_by(name=imported_name).first():
                for i in range(100):
                    if QuestionSet.query.filter_by(name=imported_name).first():
                        imported_name = f"{question_set_json['name']} ({i+1})"
                    else:
                        break

            # First create the tool...                    
            question_set = QuestionSet(
                name = imported_name,
                date_created = func.now(),
                date_modified = func.now(),
                description = question_set_json['description'],
                default_process_id = question_set_json['default_process'],
                owner = current_user
            )
            try:
                question_set.color = question_set_json['color']
            except:
                question_set.color = "#FFFFFF"
            try:            
                question_set.text_color = question_set_json['text_color']
            except:
                question_set.text_color = "#000000"

            # Import forbidden and mandatory tags...
            if request.form.get('create_tags'):
                newly_created_tags = []
                for forbidden_tag in question_set_json['forbidden_tags']:
                    tag = Tag.query.filter_by(name=forbidden_tag['name']).first()
                    if tag is None: #Tag needs to be created first
                        tag = Tag(name = forbidden_tag['name'])
                        db.session.add(tag)
                        newly_created_tags.append(tag.name)
                    question_set.forbidden_tags.append( tag )
                for mandatory_tag in question_set_json['mandatory_tags']:
                    tag = Tag.query.filter_by(name=mandatory_tag['name']).first()
                    if tag is None: #Tag needs to be created first
                        tag = Tag(name = mandatory_tag['name'])
                        db.session.add(tag)
                        newly_created_tags.append(tag.name)
                    question_set.mandatory_tags.append(tag)

            # Then create the questions...
            order_counter = 1
            for question_json in question_set_json['questions']:
                question = Question(
                    name = question_json['name'],
                    description = question_json['description'],
                    allow_motivation = question_json['allow_motivation'],
                    allow_choice = question_json['allow_choice'],
                    allow_multiselect = question_json['allow_multiselect'],
                    allow_weight = question_json['allow_weight'],
                    order = order_counter
                )
                for required_active_tag in question_json['required_active_tags']:
                    tag = Tag.query.filter_by(name=required_active_tag['name']).first()
                    if tag is None: #Tag needs to be created first
                        tag = Tag(name = required_active_tag['name'])
                        db.session.add(tag)
                        newly_created_tags.append(tag.name)
                    question.required_active_tags.append( tag )
                order_counter += 1
                for option_json in question_json['options']:
                    option = Option( name = option_json['name'])
                    for tag_json in option_json['tags']:
                        tag = Tag.query.filter_by(name=tag_json).first()
                        if tag is None: #Tag needs to be created first
                            tag = Tag(name = tag_json)
                            db.session.add(tag)
                            newly_created_tags.append(tag.name)
                        option.tags.append(tag)
                    question.options.append(option)
                question_set.questions.append(question)

            db.session.add(question_set)
            db.session.commit()
            return redirect(url_for('tools.design_question_set', question_set_id=question_set.id))
    return render_template('tools/import_question_set.html')


@tools.route('/view_question_set/<int:question_set_id>', methods=['GET', 'POST'])
@login_required
def view_question_set(question_set_id):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question_set = QuestionSet.query.get(question_set_id)
    return render_template('tools/view_question_set.html', question_set=question_set)


@tools.route('/design_question_set/<int:question_set_id>', methods=['GET', 'POST'])
@login_required
def design_question_set(question_set_id):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question_set = QuestionSet.query.get(question_set_id)
    tags = Tag.query.order_by(Tag.name)

    form = AddQuestionForm()
    add_mandatory_tag_form = AddTagToQuestionSet()

    add_forbidden_tag_form = AddTagToQuestionSet()
    add_mandatory_tag_form.tag.choices = [(tag.id, tag.name) for tag in tags]
    add_forbidden_tag_form.tag.choices = [(tag.id, tag.name) for tag in tags]

    if form.validate_on_submit():
        # Add question
        order = Question.query.order_by(Question.order.desc()).first().order + 1
        question = Question(name = form.name.data, question_set=question_set, allow_weight=question_set.default_allow_weights, order=order)
        db.session.add(question)
        for new_order, current_question in enumerate(Question.query.order_by(Question.question_set_id).order_by(Question.order)):
            current_question.order = new_order * 2 
        db.session.commit()
        return redirect(url_for('tools.design_question_set', question_set_id=question_set_id))
    # if add_mandatory_tag_form.validate_on_submit():
    if "mandatory" in request.form:  
        # Add mandatory tag
        tag = Tag.query.get(add_mandatory_tag_form.tag.data)
        question_set.mandatory_tags.append(tag)
        db.session.commit()
        return redirect(url_for('tools.design_question_set', question_set_id=question_set_id))
    # if add_forbidden_tag_form.validate_on_submit():
    if "forbidden" in request.form:
        # Add forbidden tag
        tag = Tag.query.get(add_forbidden_tag_form.tag.data)
        question_set.forbidden_tags.append(tag)
        db.session.commit()
        return redirect(url_for('tools.design_question_set', question_set_id=question_set_id))       
    return render_template('tools/design_question_set.html', question_set=question_set, form=form, add_mandatory_tag_form=add_mandatory_tag_form, add_forbidden_tag_form=add_forbidden_tag_form)


@tools.route('/delete_question_set/<int:question_set_id>', methods=['GET', 'POST'])
@login_required
def delete_question_set(question_set_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question_set = QuestionSet.query.get(question_set_id)
    if len(question_set.worksessions) > 0:
        return render_template('error/worksessions_present_error.html', worksessions=question_set.worksessions)
    db.session.delete(question_set)
    db.session.commit()
    return redirect(url_for('tools.index'))


@tools.route('/design_question_set/<int:question_set_id>/remove_tag/<string:taglist>/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def remove_tag_from_question_set(question_set_id, taglist, tag_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question_set = QuestionSet.query.get(question_set_id)
    tag = Tag.query.get(tag_id)

    if taglist == 'mandatory':
        question_set.mandatory_tags.remove(tag)

    if taglist == 'forbidden':
        question_set.forbidden_tags.remove(tag)

    db.session.commit()
    return redirect(url_for('tools.design_question_set', question_set_id=question_set_id))    


@tools.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question = Question.query.get(question_id)
    form = QuestionForm()

    if form.validate_on_submit():
        question.name = form.name.data
        question.description = form.description.data
        question.allow_motivation = form.allow_motivation.data
        question.allow_choice = form.allow_choice.data
        question.allow_multiselect = form.allow_multiselect.data
        question.allow_weight = form.allow_weight.data
        db.session.commit()
        return redirect(url_for('tools.design_question_set', question_set_id=question.question_set.id))
    elif request.method == 'GET':
        form.name.data = question.name
        form.description.data = question.description
        form.allow_motivation.data = question.allow_motivation
        form.allow_choice.data = question.allow_choice
        form.allow_multiselect.data = question.allow_multiselect
        form.allow_weight.data = question.allow_weight
    return render_template('tools/edit_question.html', form=form, question=question)



@tools.route('/design_question_set/<int:question_set_id>/edit_question/<int:question_id>/move/<int:dir>', methods=['GET', 'POST'])
@login_required
def question_move(question_set_id, question_id, dir):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')

    question = Question.query.get(question_id)

    for new_order, current_question in enumerate(Question.query.order_by(Question.question_set_id).order_by(Question.order)):
        current_question.order = new_order * 2 
        # The order numbers are all even so the question to be moved can fit in between two questions.
        # This action doesn't change the actual order of all the questions, because they are also retrieved in order. 
        # They may get a new number. The problem is that the questions are moved within the question set, and there may
        # questions in the database in between that are not part of the current question set. That's why the 
        # questions are sorted by squestion set first.
    
        if current_question == question:
            if dir == 1: # Move the question down in the order
                current_question.order = ( new_order * 2 ) - 3 # Move it before the previous question
            if dir == 0: # Move the question up in the order
                current_question.order = ( new_order * 2 ) + 3
    db.session.commit()
    return redirect(url_for('tools.design_question_set', question_set_id=question.question_set.id))


@tools.route('/edit_question/<int:question_id>/edit_options', methods=['GET', 'POST'])
@login_required
def edit_question_options(question_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question = Question.query.get(question_id)
    form=OptionForm()

    if form.validate_on_submit():
        option = Option(name = form.name.data, question=question)
        for new_order, current_option in enumerate(Option.query.order_by(Option.question_id).order_by(Option.order)):
        # See the move question function for an explanation on this procedure.
            current_option.order = new_order * 2 
        db.session.add(option)
        db.session.commit()
        return redirect(url_for('tools.edit_question_options', question_id=question_id))
    elif request.method == 'GET':
        pass
    return render_template('tools/edit_options.html', form=form, question=question)


@tools.route('/delete_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def delete_question(question_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question = Question.query.get(question_id)
    question_set = QuestionSet.query.get(question.question_set.id)

    # Check to see if answers for this question exist. In that case, deletion is not possible
    answers = Answer.query.filter_by(question=question).all()
    if len(answers) > 0:
        return render_template('error/answers_present_error.html', worksessions=question_set.worksessions)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('tools.design_question_set', question_set_id=question_set.id))


@tools.route('/edit_required_tags/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_required_tags(question_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    question = Question.query.get(question_id)
    tags = Tag.query.order_by(Tag.name)
    form = AddRequiredTagToQuestionForm()
    form.tag.choices = [(tag.id, tag.name) for tag in tags]

    if form.validate_on_submit():
        tag = Tag.query.get(form.tag.data)
        question.required_active_tags.append(tag)
        db.session.commit()
        return redirect(url_for('tools.edit_required_tags', question_id=question_id))
    return render_template('tools/edit_required_tags.html', question=question, form=form)

@tools.route('/remove_tag_from_required_tags/<int:question_id>/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def remove_tag_from_required_tags(question_id, tag_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    
    question = Question.query.get(question_id)
    tag = Tag.query.get(tag_id)
    question.required_active_tags.remove(tag)

    db.session.commit()
    return redirect(url_for('tools.edit_required_tags', question_id=question_id))


@tools.route('/edit_option/<int:option_id>', methods=['GET', 'POST'])
@login_required
def edit_option(option_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    option = Option.query.get(option_id)
    form = OptionForm()
    form.submit.label.text = 'Bevestigen'

    if form.validate_on_submit():
        option.name = form.name.data
        db.session.commit()
        return redirect(url_for('tools.edit_question_options', question_id=option.question_id))
    elif request.method == 'GET':
        form.name.data = option.name
    return render_template('tools/edit_option.html', option=option, form=form)


@tools.route('/edit_option/<int:option_id>/move/<int:dir>', methods=['GET', 'POST'])
@login_required
def option_move(option_id, dir):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een tool te ontwerpen.')
    
    option = Option.query.get(option_id)

    for new_order, current_option in enumerate(Option.query.order_by(Option.question_id).order_by(Option.order)):
        # See the move question function for an explanation on this procedure.
        current_option.order = new_order * 2 # The order numbers are all even so the question to be moved can fit in between two questions.
        if current_option == option:
            if dir == 1: # Move the question down in the order
                current_option.order = ( new_order * 2 ) - 3 # Move it before the previous question
            if dir == 0: # Move the question up in the order
                current_option.order = ( new_order * 2 ) + 3
    db.session.commit()
    return redirect(url_for('tools.edit_question_options', question_id=option.question.id))


@tools.route('/delete_option/<int:option_id>', methods=['GET', 'POST'])
@login_required
def delete_option(option_id):
    option = Option.query.get(option_id)
    db.session.delete(option)
    db.session.commit()
    return redirect(url_for('tools.edit_question_options', question_id=option.question_id))


@tools.route('/edit_option/<int:option_id>/edit_tags', methods=['GET', 'POST'])
@login_required
def edit_tag_assignment(option_id):
    option = Option.query.get(option_id)
    tags = Tag.query.order_by(Tag.name)
    return render_template('tools/edit_tag_assignment.html', option=option, tags=tags)


@tools.route('/edit_option/<int:option_id>/toggle_tag/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def toggle_tag(option_id, tag_id):
    option = Option.query.get(option_id)
    tag = Tag.query.get(tag_id)
    if tag in option.tags:
        option.tags.remove(tag)
    else:
        option.tags.append(tag)
    db.session.commit()
    return redirect(url_for('tools.edit_tag_assignment', option_id=option.id))


@tools.route('/tag/<int:tag_id>')
@login_required
def tag(tag_id):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
   
    return render_template('tools/tag_info.html', 
                           edit_catalog_allowed=current_user.role.edit_catalog, 
                           tag=Tag.query.get(tag_id),
                           question_sets=QuestionSet.query.order_by(QuestionSet.name),
                           instrument_tag_assignments=InstrumentTagAssignment.query.order_by(InstrumentTagAssignment.id))


@tools.route('/tags', methods=['GET', 'POST'])
@login_required
def tags():
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    form = TagForm()
    tags = Tag.query.order_by(Tag.name)
    if form.validate_on_submit():
        tag = Tag(name = form.name.data)
        db.session.add(tag)
        db.session.commit()
        return redirect(url_for('tools.tags'))
    elif request.method == 'GET':
        pass
    return render_template('tools/tags.html', edit_catalog_allowed=current_user.role.edit_catalog, tags=tags, form=form)


@tools.route('/tag/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    form = TagForm()
    tag = Tag.query.get(tag_id)
    if form.validate_on_submit():
        tag.name = form.name.data
        db.session.commit()
        return redirect(url_for('tools.tags'))
    elif request.method == 'GET':
        form.name.data = tag.name
    return render_template('tools/edit_tag.html', form=form, tag=tag)


@tools.route('/tag/<int:tag_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_tag(tag_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    tag = Tag.query.get(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for('tools.tags'))