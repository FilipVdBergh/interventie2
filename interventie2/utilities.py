from flask import url_for
from flask_login import current_user
from interventie2.models import User, Instrument, Remark, Tag, InstrumentTagAssignment, QuestionSet, Question, Answer, Option, Worksession, Plan

def search(search_text_all, worksessions=True, catalog=True, tools=True, users=True):

    print(f'worksession: {worksessions}; catalog: {catalog}; tools: {tools}; users: {users}')

    search_results = {'tag':[],
                      'gebruiker': [],
                      'instrument': [],
                      'selectietool': [],
                      'vraag': [],
                      'antwoordoptie': [],
                      'werksessie': [],
                      'antwoord op vraag': [],
                      'interventieplan': []}
    user = current_user

    for search_text in search_text_all.split("/"):
        
        # Search tags
        if worksessions or catalog:
            if current_user.role.edit_questionnaire or user.role.edit_catalog:
                for item in Tag.query.order_by(Tag.name):
                    if search_text.lower() in item.name.lower():
                        search_results['tag'].append({'name': item.name,
                                    'context': 'Tag bij antwoordopties en instrumenten.',
                                    'url': url_for('analysis.tag', tag_id=item.id)})

        # Search users
        if users:
            if True: # (no special permissions required)
                for item in User.query.order_by(User.name):
                    if search_text.lower() in item.name.lower():
                        search_results['gebruiker'].append({'name': item.name,
                                    'context': item.description,
                                    'url': url_for('admin.user', id=item.id)})

        # Search instruments
        if catalog:
            if True: # (no special permissions required)
                for item in Instrument.query.order_by(Instrument.name):
                    if search_text.lower() in item.name.lower() or search_text.lower() in item.description or search_text.lower() in item.introduction or search_text.lower() in item.considerations or search_text.lower() in item.examples:
                        search_results['instrument'].append({'name': item.name,
                                    'context': item.introduction,
                                    'url': url_for('catalog.show_instrument', id=item.id)})

        # Search selection tools
        if tools:
            if current_user.role.edit_questionnaire:
                for item in QuestionSet.query.order_by(QuestionSet.name):
                    if search_text.lower() in item.name.lower() or search_text in item.description.lower():
                        search_results['selectietool'].append({'name': item.name,
                                    'context': item.description,
                                    'url': url_for('tools.design_question_set', question_set_id=item.id)})

        # Search questions in selection tools
        if tools:
            if current_user.role.edit_questionnaire:
                for item in Question.query.order_by(Question.name):
                    if search_text.lower() in item.name.lower() or search_text in item.description.lower():
                        search_results['vraag'].append({'name': item.name,
                                    'context': f'Vraag in  in {item.question_set.name}. {item.description}',
                                    'url': url_for('tools.edit_question', question_id=item.id)})

        # Search options in selection tools
        if tools:
            if current_user.role.edit_questionnaire:
                for item in Option.query.order_by(Option.name):
                    if search_text.lower() in item.name.lower():
                        search_results['antwoordoptie'].append({'name': item.name,
                                    'context': f'Antwoordoptie bij vraag {item.question.name} in selectietool {item.question.question_set.name}.',
                                    'url': url_for('tools.edit_option', option_id=item.id)})

        # Search worksessions. Permissions are a but strange here because some users can see all worksessions. 
        if worksessions:
            for item in Worksession.query.order_by(Worksession.name):
                if search_text.lower() in item.name.lower() or search_text in item.description.lower() or search_text in item.effect.lower() or search_text in item.conclusion.lower() or search_text in item.participants.lower() or search_text in item.creator.name.lower():
                    if current_user.role.see_all_worksessions or item in current_user.allowed_worksessions:
                        search_results['werksessie'].append({'name': item.name,
                                    'context': item.description,
                                    'url': url_for('main.show_worksession', worksession_id=item.id)})

        # Search answers
        if worksessions:
            for item in Answer.query.order_by(Answer.motivation):
                if search_text.lower() in item.motivation.lower():
                    if current_user.role.see_all_worksessions or item in current_user.allowed_worksessions:
                        search_results['antwoord op vraag'].append({'name': item.motivation,
                                    'context': f'Antwoord op vraag {item.question.name} in {item.worksession.name}',
                                    'url': url_for('main.show_worksession', worksession_id=item.id)})

        # Search intervention plans
        if worksessions:
            for item in Plan.query.order_by(Plan.description):
                if search_text.lower() in item.description.lower() or search_text in item.conclusion.lower():
                    if current_user.role.see_all_worksessions or item in current_user.allowed_worksessions:
                        search_results['interventieplan'].append({'name': f'{item.description} ({item.worksession.name})',
                                    'context': item.conclusion,
                                    'url': url_for('main.show_plan', worksession_id=item.worksession.id, plan_id=item.id)})

    return search_results