from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import current_user, login_required, fresh_login_required
from interventie2.models import db
from interventie2.models import User, Role, Process
from interventie2.forms import RegisterForm, EditUserForm, ChangePasswordForm

admin = Blueprint('admin', __name__,
                  template_folder='templates',
                  static_folder='static',
                  static_url_path='assets')


@admin.route('/initialize')
def initialize():
    """Initializes the database. This function creates the necessary roles and a single admin user called root/root.
    This function should refuse to run if a root user (id=1) already exists."""    

    print('== DATABASE INITIALIZATION ======================================')
    try:
        root_user = User.query.get(1)
    except:
        root_user = None

    if root_user is None:
        print('Creating structure...')
        db.create_all()

        print('Populating permissions table...')
        root = Role(name='root',             see_app_info=True, see_all_sessions=True,  edit_catalog=True,  edit_questionnaire=True,  edit_users=True, demo=False)
        admin = Role(name='admin',           see_app_info=True, see_all_sessions=True,  edit_catalog=True,  edit_questionnaire=True,  edit_users=True, demo=False)
        maintainer = Role(name='maintainer', see_app_info=False, see_all_sessions=True,  edit_catalog=True,  edit_questionnaire=False, edit_users=False, demo=False)
        user = Role(name='user',             see_app_info=False, see_all_sessions=False, edit_catalog=False, edit_questionnaire=False, edit_users=False, demo=False)
        demo = Role(name='demo',             see_app_info=False, see_all_sessions=False, edit_catalog=False, edit_questionnaire=False, edit_users=False, demo=True)
        for new_role in [root, admin, maintainer, user, demo]:
            db.session.add(new_role)

        print('Creating root user (root:root). Remember to change the password!')
        root_user = User(name='root', 
                         email=current_app.config['MAINTAINER_EMAIL'], 
                         role_id=1, 
                         description='Gemaakt bij initialisatie van de database. **Vergeet niet het wachtwoord te veranderen**.',)
        root_user.set_password('root')
        db.session.add(root_user)

        print('Finsihing touches...')
        standard_process = Process(name='Presenteer alle vragen tegelijk')
        wizard_process = Process(name='Presenteer één vraag tegelijk')
        for new_process in [standard_process, wizard_process]:
            db.session.add(new_process)

        db.session.commit()
        print('Done.')
        print('================================================================')
        return redirect(url_for('main.index'))
    
    print('Root user exists, operation cancelled.')
    print('================================================================')
    return('De root user (id=1) bestaat al. Het initaliseren van de database is niet uitgevoerd.')


@admin.route('/user/<int:id>')
@admin.route('/user')
@login_required
def user(id=None):
    if id is None: # Deze functie kan worden aangeroepen zonder argumenten en laat dan de current_user zien.
        id = current_user.id
    return render_template('admin/user.html', user=User.query.get(id))


@admin.route('/users')
@login_required
def index():
    list_of_users = User.query.order_by(User.id)
    return render_template('admin/index.html', users=list_of_users)


@admin.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.role.edit_users: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een gebruiker toe te voegen.')

    form = RegisterForm()
    form.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id)]
    if form.validate_on_submit():
        user = User(name = form.name.data, 
                    role_id = form.role.data,
                    email = form.email.data,
                    description = form.description.data,
                    link = form.link.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('admin.index'))
    return render_template('admin/register.html', form=form)


@admin.route('/user/<int:user_id>/password', methods=['GET', 'POST'])
@fresh_login_required
def change_password(user_id):
    user = User.query.get(user_id)
    if not user.edit_allowed(): 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om gebruikerswachtwoord te wijzigen.')
    
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        return redirect(url_for('admin.user', id = current_user.id))
    return render_template('admin/change_password.html', form=form, user=user)       


@admin.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get(user_id)
    if not user.edit_allowed(): 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om gebruiker te wijzigen.')

    form = EditUserForm()
    form.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.id)]
    if form.validate_on_submit():
        user.name = form.name.data
        if current_user.role.edit_users:
            user.role_id = form.role.data
        user.email = form.email.data
        user.description = form.description.data
        user.link = form.link.data
        db.session.commit()
        return redirect(url_for('admin.user', id=user.id))
    elif request.method == 'GET':
        form.name.data = user.name
        form.role.data = user.role_id
        form.email.data = user.email
        form.description.data = user.description
        form.link.data = user.link
    return render_template('admin/edit_user.html', form=form, user=user)


@admin.route('/user/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user.edit_allowed(): 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om gebruiker te verwijderen.')

    db.session.delete(user)
    try:
        db.session.commit()
    except: 
        db.session.rollback()
        return render_template('error/index.html', title='Kan gebruiker niet verwijderen', message='Kan de gebruiker niet verwijderen. Zorg ervoor dat alle instrumenten en tools aan een andere gebruiker zijn toegewezen.')        
        
    return redirect(url_for('admin.index'))


@admin.route('/roles')
@login_required
def roles():
    roles = Role.query.order_by()
    return render_template('admin/roles.html', roles=roles)


@admin.route('/info')
@login_required
def info():
    if current_user.role.see_app_info:
        return render_template('admin/info.html')
    return("Hoe ben je hier terecht gekomen?")