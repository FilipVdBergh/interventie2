import os
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from interventie2.models import db
from interventie2.models import User, Instrument, Remark, Tag, InstrumentTagAssignment, QuestionSet, Question, Answer, Option, Worksession, Plan
from interventie2.forms import SearchForm
from sqlalchemy.sql import func, text
import simplejson as json

analysis = Blueprint('analysis', __name__,
                  template_folder='templates',
                  static_folder='static',
                  static_url_path='assets')



@analysis.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()

    if form.validate_on_submit():
        search_text = form.search_text.data.lower()
        found_tags = []
        for tag in Tag.query.order_by(Tag.name):
            if search_text in tag.name.lower():
                found_tags.append(tag)
        found_instruments = []
        for instrument in Instrument.query.order_by(Instrument.name):
            if search_text in instrument.name.lower() or search_text in instrument.description.lower() or search_text in instrument.considerations.lower() or search_text in instrument.examples.lower() or search_text in instrument.owner.name.lower():
                found_instruments.append(instrument)
        found_question_sets = []
        for question_set in QuestionSet.query.order_by(QuestionSet.name):
            if search_text in question_set.name.lower() or search_text in question_set.description.lower() or search_text in question_set.owner.name.lower():
                found_question_sets.append(question_set)
        found_questions = []
        for question in Question.query.order_by(Question.name):
            if search_text in question.name.lower():
                found_questions.append(question)
        found_options = []
        for option in Option.query.order_by(Option.name):
            if search_text in option.name.lower():
                found_options.append(option)
        found_worksessions = []
        for worksession in Worksession.query.order_by(Worksession.name):
            if search_text in worksession.name.lower() or search_text in worksession.description.lower() or search_text in worksession.effect.lower() or search_text in worksession.conclusion.lower() or search_text in worksession.participants.lower() or search_text in worksession.creator.name.lower():
                found_worksessions.append(worksession)
        found_answers = []
        for answer in Answer.query.order_by(Answer.motivation):
            if search_text in answer.motivation.lower():
                found_answers.append(answer)
        found_plans = []
        for plan in Plan.query.order_by(Plan.description):
            if search_text in plan.description.lower() or search_text in plan.conclusion.lower():
                found_plans.append(plan)
        found_users = []
        for user in User.query.order_by(User.name):
            if search_text in user.name.lower() or search_text in user.description.lower():
                found_users.append(user)

        return render_template('analysis/results.html', 
                                form=form,
                                search_text=search_text,
                                found_tags=found_tags,
                                found_instruments=found_instruments,
                                found_question_sets=found_question_sets,
                                found_questions=found_questions,
                                found_options=found_options,
                                found_worksessions=found_worksessions,
                                found_answers=found_answers,
                                found_plans=found_plans,
                                found_users=found_users)
    return render_template('analysis/index.html', form=form)


@analysis.route('/tag/<int:tag_id>')
@login_required
def tag(tag_id):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
   
    return render_template('analysis/tag.html', 
                           edit_catalog_allowed=current_user.role.edit_catalog, 
                           tag=Tag.query.get(tag_id),
                           question_sets=QuestionSet.query.order_by(QuestionSet.name),
                           instrument_tag_assignments=InstrumentTagAssignment.query.order_by(InstrumentTagAssignment.id))