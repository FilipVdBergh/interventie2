from docx.shared import Cm

def add_title(document, title):
    document.add_heading(title, level=0)


def add_remarks(document, remarks):
    document.add_heading('Opmerkingen bij deze export', level=1)
    document.add_paragraph(remarks)


def add_session_info(document, session):
    section = document.sections[0]
    footer = section.footer.paragraphs[0]
    footer.text = f'Verslag {session.name} op {session.date}.'

    document.add_heading('Informatie over de casus', level=1)

    document.add_heading('Beschrijving', level=2)
    document.add_paragraph(session.description)
    document.add_heading('Beoogd effect', level=2)
    document.add_paragraph(session.effect)
    document.add_heading('Definitieve overwegingen', level=2)
    document.add_paragraph(session.conclusion)

    if session.link_to_page is not None:
        document.add_heading('Link naar project', level=2)
        document.add_paragraph(session.link_to_page)

    document.add_heading('Informatie over de sessie', level=1)

    document.add_heading('Datum', level=2)
    document.add_paragraph(session.date)
    document.add_heading('Deelnemers', level=2)
    document.add_paragraph(session.participants)


def add_session_process(document, session):
    document.add_heading('Werkwijze', level=2)
    document.add_paragraph(f'De gebruikte tool was {session.question_set.name}. De tool werd gebruikt met het volgende proces: {session.process.name}.')


def add_answers(document, session):
    document.add_heading(f'Antwoorden op {session.question_set.name}', level=1)
    for question in sorted(session.question_set.questions, key=lambda order: getattr(order, 'order')):
        if question.is_category:
            document.add_heading(question.name, level=2)
            if question.description != "":
                document.add_paragraph(question.description)
        else:
            document.add_paragraph(question.name, style='Vraag')
            if question.description != "":
                document.add_paragraph(question.description)
            for option in question.options:
                if session.is_option_selected(option):
                    document.add_paragraph(option.name, style='Optie')
            for answer in session.answers:
                if answer.question == question:
                    document.add_paragraph(answer.motivation)


def add_suggestions_table(document, suggestions):
    document.add_heading('Advies op basis van de werksessie', level=1)
    document.add_paragraph('Deze lijst van suggesties voor interventies is gebaseerd op de antwoorden gekozen in de sessie. In het volgende hoofdstuk staan de instrumenten verder uitgewerkt.')
    
    table = document.add_table(rows=1, cols=3, style='interventie.afm.nl')
    
    header = table.rows[0].cells
    header[0].text = 'Instrument'
    header[1].text = 'Score'
    header[1].width = Cm(1.0)
    header[2].text = 'Omschrijving'
    header[2].width = Cm(16.5)
    for instrument, score in suggestions:
        row = table.add_row().cells
        row[0].text = instrument.name
        row[1].text = str(score)
        row[1].width = Cm(1.0)
        row[2].text = instrument.introduction
        row[2].width = Cm(16.5)


def add_instrument(document, instrument, start_level=2):
    document.add_heading(instrument.name, level=start_level)
    document.add_paragraph(instrument.introduction)
    document.add_heading('Beschrijving', level=start_level+1)
    document.add_paragraph(instrument.description)
    document.add_heading('Overwegingen bij gebruik', level=start_level+1)
    document.add_paragraph(instrument.considerations)
    document.add_heading('Voorbeelden', level=start_level+1)
    document.add_paragraph(instrument.examples)
    document.add_heading('Links', level=3)
    document.add_paragraph(instrument.links)
    document.add_heading('Tags', level=3)
    plustags = document.add_paragraph('Tags met een factor groter dan 1: ')
    mintags =  document.add_paragraph('Tags met een factor kleiner dan 1: ')
    for tag_assignment in instrument.tags:
        if tag_assignment.multiplier >= 1:
            plustags.add_run(f'{tag_assignment.tag.name}: {tag_assignment.multiplier}', style='PlusTag')
            plustags.add_run(' ')
        else:
            mintags.add_run(f'{tag_assignment.tag.name}: {tag_assignment.multiplier}', style='MinTag')
            plustags.add_run(' ')
    
def add_calculation(document, explanation):
    document.add_heading('Berekening', level=3)
    # if explanation.get 'forbidden_tags_found'] is not None:
    #     pass
    # if explanation['mandatory_tags_not_found'] is not None:
    #     pass
    # for tag in explanation.tags:
    #     pass