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



# @analysis.route('/', methods=['GET', 'POST'])
# @login_required
# def index():
#     form = SearchForm()

#     if form.validate_on_submit():
#         search_text = form.search_text.data
#         search_results = search(search_text)
#         return render_template('analysis/results.html', 
#                                 form=form,
#                                 search_text=search_text,
#                                 search_results=search_results)
#     return render_template('analysis/index.html', form=form)



@analysis.route('/')
@login_required
def index():
    return render_template('analysis/index.html')

@analysis.route('/search')
@login_required
def search():
    search_text = request.args.get('q')
    search_results = search_database(search_text)
    return render_template('analysis/results.html', 
                            search_text=search_text,
                            search_results=search_results)