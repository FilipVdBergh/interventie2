import os
from flask import Blueprint, current_app, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from interventie2.models import db
from interventie2.models import User, Instrument, Remark, Tag, InstrumentTagAssignment
from interventie2.forms import InstrumentsForm, RemarkForm, TagForm, TagInstrumentAssignmentForm
from sqlalchemy.sql import func, text
import simplejson as json

catalog = Blueprint('catalog', __name__,
                  template_folder='templates',
                  static_folder='static',
                  static_url_path='assets')



@catalog.route('/')
@catalog.route('/filter/<int:tag_id>')
def index(tag_id=None):
    # Login is niet nodig om de catalogus in te zien, maar om te wijzigen natuurlijk wel.
    if current_user.is_authenticated:
        edit_catalog_allowed = current_user.role.edit_catalog
    else:
        edit_catalog_allowed = False

    filter_tag = Tag.query.get(tag_id)
    if tag_id is not None:        
        list_of_instruments = []
        for instrument in Instrument.query.order_by(Instrument.name):
            for instrument_tag_assignment in instrument.tags:
                if instrument_tag_assignment.tag == filter_tag:
                    list_of_instruments.append(instrument)    
    else:
        list_of_instruments = Instrument.query.order_by(Instrument.name)


    return render_template('catalog/index.html', 
                           edit_catalog_allowed=edit_catalog_allowed, 
                           instruments=list_of_instruments,
                           filter_tag=filter_tag,
                           tags = Tag.query.order_by(Tag.name))


@catalog.route('/instrument/<int:id>')
def show_instrument(id):
    # Login is niet nodig om de catalogus in te zien, maar om te wijzigen natuurlijk wel.
    if current_user.is_authenticated:
        edit_catalog_allowed = current_user.role.edit_catalog
    else:
        edit_catalog_allowed = False
    instrument = Instrument.query.get(id)
    list_of_instruments = Instrument.query.order_by(Instrument.name)
    return render_template('catalog/instrument.html', edit_catalog_allowed=edit_catalog_allowed, instrument=instrument, instruments=list_of_instruments)


@catalog.route('/instrument/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_instrument(id):
    if not current_user.role.edit_catalog:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een instrument te wijzigen.')
    
    list_of_instruments = Instrument.query.order_by(Instrument.name)
    instrument = Instrument.query.get(id)
    form = InstrumentsForm()
    form.owner.choices = [(user.id, user.name) for user in User.query.order_by(User.name)]
    if form.validate_on_submit():
        instrument.name = form.name.data
        instrument.introduction = form.introduction.data
        instrument.referenced_elsewhere = form.referenced_elsewhere.data
        instrument.reference_link = form.reference_link.data
        instrument.description = form.description.data
        instrument.considerations = form.considerations.data
        instrument.examples = form.examples.data
        instrument.links = form.links.data
        instrument.owner_id = form.owner.data
        instrument.date_modified = func.now()
        db.session.commit()
        return redirect(url_for('catalog.show_instrument', id=instrument.id))
    elif request.method == 'GET':
        form.name.data = instrument.name
        form.introduction.data = instrument.introduction
        form.referenced_elsewhere.data = instrument.referenced_elsewhere
        form.reference_link.data = instrument.reference_link
        form.description.data = instrument.description
        form.considerations.data = instrument.considerations
        form.examples.data = instrument.examples
        form.links.data = instrument.links
        form.owner.data = instrument.owner_id

    return render_template('catalog/edit_instrument.html', form=form, instruments=list_of_instruments, instrument=instrument, edit_catalog_allowed=current_user.role.edit_catalog)


@catalog.route('/instrument/add', methods=['GET', 'POST'])
@login_required
def add_instrument():
    if not current_user.role.edit_catalog:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een instrument toe te voegen.')

    form = InstrumentsForm()
    form.owner.choices = [(user.id, user.name) for user in User.query.order_by(User.name)]
    form.owner.data = current_user.id
    if form.validate_on_submit():
        instrument = Instrument(name = form.name.data, 
                    date_created = func.now(),
                    date_modified = func.now(),
                    introduction = form.introduction.data,
                    referenced_elsewhere = form.referenced_elsewhere.data,
                    reference_link = form.reference_link.data,
                    description = form.description.data,
                    considerations = form.considerations.data,
                    examples = form.examples.data,
                    links = form.links.data,
                    owner = current_user)
        db.session.add(instrument)
        db.session.commit()
        return redirect(url_for('catalog.show_instrument', id=instrument.id))
    
    return render_template('catalog/edit_instrument.html', form=form, edit_catalog_allowed=current_user.role.edit_catalog, instrument=None)


@catalog.route('/instrument/import', methods=['GET', 'POST'])
@login_required
def import_instrument():
    if not current_user.role.edit_catalog: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een instrument te importeren.')
    
    if request.method == "POST":
        uploaded_file = request.files['file']

        if uploaded_file.filename != '':
            instrument_file = os.path.join(current_app.static_folder, 'import', uploaded_file.filename)
            uploaded_file.save(instrument_file)

            f = open(instrument_file)
            instrument_json = json.load(f)

            # Check if the filetype and version match
            if not(instrument_json['filetype'] == 'instrument'):
                return render_template('error/index.html', title='Verkeerd bestandstype', message=f"Het bestand beschrijft geen instrument (filetype: {instrument_json['filetype']}). Importeren is niet mogelijk.")
            if not(instrument_json['filetype_version'] == current_app.config['FILETYPE_VERSION']):
                return render_template('error/index.html', title='Verkeerde indelingsversie', message=f"Het bestand heeft indelingsversie {instrument_json['filetype_version']}, en de applicatie verwacht indelingsversie {current_app.config['FILETYPE_VERSION']}. Importeren is niet mogelijk.")


            # Rename instrument in case of a duplicate instrument name in the database:
            imported_name = instrument_json['name']
            if Instrument.query.filter_by(name=imported_name).first():
                for i in range(100):
                    if Instrument.query.filter_by(name=imported_name).first():
                        imported_name = f"{instrument_json['name']} ({i+1})"
                    else:
                        break

            # First create the instrument...                    
            instrument = Instrument(
                name = imported_name,
                date_created = func.now(),
                date_modified = func.now(),
                introduction = instrument_json['introduction'],
                description = instrument_json['description'],
                referenced_elsewhere = instrument_json['referenced_elsewhere'],
                reference_link = instrument_json['reference_link'],
                considerations = instrument_json['considerations'],
                examples = instrument_json['examples'],
                links = instrument_json['links'],
                owner = current_user
            )
            db.session.add(instrument)

            # Then create the tags...
            if request.form.get('create_tags'):
                newly_created_tags = []
                for new_tag in instrument_json['tags']:
                    tag = Tag.query.filter_by(name=new_tag['name']).first()
                    if tag is not None:
                        # Tag already in tag list
                        instrument_tag_assignment = InstrumentTagAssignment(instrument = instrument,
                                                                    tag = tag,
                                                                    weight = new_tag['weight'],
                                                                    multiplier = new_tag['multiplier'])
                    else:
                        #Tag needs to be created first
                        tag = Tag(name = new_tag['name'])
                        newly_created_tags.append(tag.name)
                        instrument_tag_assignment = InstrumentTagAssignment(instrument = instrument,
                                                                    tag = tag,
                                                                    weight = new_tag['weight'],
                                                                    multiplier = new_tag['multiplier'])
                        
                        db.session.add(instrument_tag_assignment)
            
            # Add remark about importing this instrument
            import_remark = f'Instrument geïmporteerd uit bestand: {uploaded_file.filename}. '
            if len(newly_created_tags) > 0:
                import_remark += f'Tags die niet in de taglijst stonden zijn aangemaakt: **{"**, **".join(newly_created_tags)}**. Deze maken nog geen onderdeel uit van een tool.'
            remark = Remark(instrument = instrument,
                    remark = import_remark,
                    sender = current_user,
                    active = True)
            db.session.add(remark)

            db.session.commit()
            return redirect(url_for('catalog.show_instrument', id=instrument.id))
    return render_template('catalog/import_instrument.html')



@catalog.route('/instrument/<int:id>/delete')
@login_required
def delete_instrument(id):
    if not current_user.role.edit_catalog: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om een instrument te verwijderen.')

    instrument = Instrument.query.get(id)
    db.session.delete(instrument)
    db.session.commit()
    return redirect(url_for('catalog.index'))


@catalog.route('/remark/<int:remark_id>', methods=['GET', 'POST'])
@login_required
def show_remark(remark_id):
    return render_template('catalog/remark.html', remark=Remark.query.get(remark_id))


@catalog.route('/instrument/<int:instrument_id>/add_remark', methods=['GET', 'POST'])
@login_required
def add_remark(instrument_id):
    form = RemarkForm()
    if form.validate_on_submit():
        remark = Remark(instrument_id = instrument_id,
                    remark = form.remark.data,
                    sender = current_user,
                    active = not form.closed.data)
        db.session.add(remark)
        db.session.commit()
        return redirect(url_for('catalog.show_instrument', id=instrument_id))

    return render_template('catalog/edit_remark.html', form=form, new_remark=True, instrument=Instrument.query.get(instrument_id), remark=None)


@catalog.route('/instrument/<int:instrument_id>/remark/<int:remark_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_remark(instrument_id, remark_id):
    form = RemarkForm()
    remark = Remark.query.get(remark_id)
    instrument = Instrument.query.get(instrument_id)
    if not remark.edit_allowed(): 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze opmerking te wijzigen.')
    if form.validate_on_submit():
        remark.instrument_id = instrument_id
        remark.remark = form.remark.data
        remark.active = not form.closed.data
        remark.date_modified = func.now()
        db.session.commit()
        return redirect(url_for('catalog.show_instrument', id=instrument_id))
    elif request.method == 'GET':
        form.remark.data = remark.remark
        form.closed.data = not remark.active
    
    return render_template('catalog/edit_remark.html', form=form, remark=remark, instrument=instrument)


@catalog.route('/instrument/<int:instrument_id>/remark/<int:remark_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_remark(instrument_id, remark_id):
    remark = Remark.query.get(remark_id)
    if not remark.edit_allowed():
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om deze opmerking te verwijderen.')
    db.session.delete(remark)
    db.session.commit()
    return redirect(url_for('catalog.show_instrument', id = instrument_id))
    


@catalog.route('/tags', methods=['GET', 'POST'])
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
        return redirect(url_for('catalog.tags'))
    elif request.method == 'GET':
        pass
    return render_template('catalog/tags.html', edit_catalog_allowed=current_user.role.edit_catalog, tags=tags, form=form)


@catalog.route('/tag/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    if not current_user.role.edit_questionnaire:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    form = TagForm()
    tag = Tag.query.get(tag_id)
    if form.validate_on_submit():
        tag.name = form.name.data
        db.session.commit()
        return redirect(url_for('catalog.tags'))
    elif request.method == 'GET':
        form.name.data = tag.name
    return render_template('catalog/edit_tag.html', form=form, tag=tag)


@catalog.route('/tag/<int:tag_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_tag(tag_id):
    if not current_user.role.edit_questionnaire: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    tag = Tag.query.get(tag_id)
    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for('catalog.tags'))


@catalog.route('/instrument/<int:id>/tags', methods=['GET', 'POST'])
@login_required
def instrument_tags(id):
    if not current_user.role.edit_catalog: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    instrument = Instrument.query.get(id)
    tag_assignments = InstrumentTagAssignment.query.filter_by(instrument_id=id)
    tags = Tag.query.order_by(Tag.name)

    form = TagInstrumentAssignmentForm()
    form.tag.choices = [(tag.id, tag.name) for tag in tags]    
    form.type.choices =  [(1, 'Plustag (factor=1)'), (0, 'Mintag (factor=0)')]

    if form.validate_on_submit():
        tag = Tag.query.get(form.tag.data)
        instrument_tag_assignment = InstrumentTagAssignment.query.filter_by(instrument=instrument, tag=tag).first()
        if instrument_tag_assignment:
            return redirect(url_for('catalog.edit_tag_assignment_to_instrument', instrument_id=id, tag_assignment_id=instrument_tag_assignment.id))
        else:
            instrument_tag_assignment = InstrumentTagAssignment(instrument = instrument,
                                                                tag = tag,
                                                                weight = form.weight.data,
                                                                multiplier = form.type.data)
            db.session.add(instrument_tag_assignment)
            db.session.commit()
    elif request.method == 'GET':
        form.weight.data = 1
    return render_template('catalog/instrument_tags.html', form=form, instrument=instrument, tag_assignments=tag_assignments, tags=tags)


@catalog.route('/instrument/<int:instrument_id>/tag/<int:tag_assignment_id>/remove', methods=['GET', 'POST'])
@login_required
def remove_tag_from_instrument(instrument_id, tag_assignment_id):
    if not current_user.role.edit_catalog:
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    tag_assignment = InstrumentTagAssignment.query.get(tag_assignment_id)
    db.session.delete(tag_assignment)
    db.session.commit()
    return redirect(url_for('catalog.instrument_tags', id=instrument_id))


@catalog.route('/instrument/<int:instrument_id>/tag/<int:tag_assignment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tag_assignment_to_instrument(instrument_id, tag_assignment_id):
    if not current_user.role.edit_catalog: 
        return render_template('error/index.html', title='Onvoldoende rechten', message='Onvoldoende rechten om tags te wijzigen.')
    instrument = Instrument.query.get(instrument_id)
    tag_assignment = InstrumentTagAssignment.query.get(tag_assignment_id)
    form = TagInstrumentAssignmentForm()

    # Onderstaande is alleen nodig voor de validatie van het formulier:
    form.type.choices =  [(1, 'Plustag (factor=1)'), (0, 'Mintag (factor=0)')]
    form.type.data = 1
    form.tag.choices = [(1, 'Tag')]
    form.tag.data = 1

    if form.validate_on_submit():
        tag_assignment.weight = form.weight.data
        tag_assignment.multiplier = form.multiplier.data
        db.session.commit()
        return redirect(url_for('catalog.instrument_tags', id=instrument_id))
    elif request.method == 'POST':
        print(form.errors)
        #TODO What is this doing here?
    elif request.method == 'GET':
        form.weight.data = tag_assignment.weight
        form.multiplier.data = tag_assignment.multiplier
    return render_template('catalog/edit_tag_assignment.html', form=form, tag_assignment=tag_assignment, instrument=instrument)
