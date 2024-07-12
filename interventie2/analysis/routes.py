import os
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from interventie2.models import db
from interventie2.models import User, Instrument, Remark, Tag, InstrumentTagAssignment, QuestionSet, Question, Answer, Option, Worksession, Plan
from interventie2.utilities import search_database
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
        search_text = form.search_text.data
        search_results = search(search_text)
        return render_template('analysis/results.html', 
                                form=form,
                                search_text=search_text,
                                search_results=search_results)
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

@analysis.route('/search')
@login_required
def search():
    search_text = request.args.get('q')
    search_results = search_database(search_text)
    return render_template('analysis/results.html', 
                            search_text=search_text,
                            search_results=search_results)