from interventie2.models import QuestionSet, Question, Option, Answer, Selection
from operator import itemgetter

class QuestionWithAnswers:
    """ This object contains a question and its options, 
    together with the answers (the motivation as well as 
    selected options. 
    This object exists because questions exist as parts of 
    a worksession, together with answers beloning to that worksession, 
    but also as design elements. 
    I think a smarter object model would have solved this
    problem as well. """

    # TODO: To simplify the app, the Advisor class could be made part of the Worksession object!
    class option_with_selection:
        def __init__(self, option, selected):
            self.option          = option
            self.selected        = selected
    def __init__(self, question, answer):
        self.id                  = question.id
        self.name                = question.name
        self.description         = question.description
        self.is_category         = question.is_category
        self.allow_motivation    = question.allow_motivation
        self.allow_choice        = question.allow_choice
        self.allow_multiselect   = question.allow_multiselect
        self.allow_weight        = question.allow_weight
        self.order               = question.order
        self.options_with_selection = []
        for option in Option.query.filter_by(question=question):
            # All options for this question will be paired with a boolean for selection status.
            ows = self.option_with_selection(option, False)
            for selected_option in Selection.query.filter_by(option=option):
                # If the option is in the list of options, selected is set to True.
                ows.selected = (selected_option.option == option)
            self.options_with_selection.append(ows)
        if answer is not None:
            self.motivation          = answer.motivation
            self.weight              = answer.weight
            self.inherit_answers     = answer.inherit_answers
            self.selection           = [selected for selected in Selection.query.filter_by(answer=answer)]
        else:
            self.motivation          = ""
            self.weight              = 1
            self.inherit_answers     = False
            self.selection           = []
    def __repr__(self):
        return f'<Q&A: {self.name}: {self.motivation}, {len(self.selected)}/{len(self.options)} selected>'


class Advisor:
    """The Advisor object takes all information necessary to generate the
    advice. The object can then be questioned to yield the entire list of
    scored instruments, the best instrument, an explanation for the score, 
    etc."""
    class active_tag:
        def __init__(self, tag, weight):
            self.tag            = tag
            self.weight         = weight

    def __init__(self, worksession=None, instruments=None):
        self.worksession            = worksession
        self.questionnaire      = [] # A list of questions_with_answers
        self.active_tags        = [] # A list of active_tag objects (with weight and multiplier)
        self.forbidden_tags     = []
        self.mandatory_tags     = []
        self.all_instruments    = [] 
        self.scored_instruments = [] # A list of instruments with their score

        self.add_worksession(worksession)
        self.add_instrument(instruments)

    def add_worksession(self, worksession):
        
        self.add_forbidden_tag(worksession.question_set.forbidden_tags)
        self.add_mandatory_tag(worksession.question_set.mandatory_tags)
        self.add_questionnaire(worksession)

    def add_instrument(self, instrument):
        if len(instrument) == 1: instrument = [instrument]
        self.all_instruments.extend(instrument)

    def add_question_with_answers(self, question_with_answers):
        if len(question_with_answers) == 1: question_with_answers = [question_with_answers]
        self.questionnaire.extend(question_with_answers)
    
    def add_questionnaire(self, worksession):	
        for question in worksession.question_set.questions:
            answer = Answer.query.filter_by(worksession=worksession, question=question).first()
            question_with_answers = QuestionWithAnswers(question, answer)
            self.questionnaire.append(question_with_answers)

    def add_forbidden_tag(self, forbidden_tag):
        self.forbidden_tags.extend(forbidden_tag)

    def add_mandatory_tag(self, mandatory_tag):
        self.mandatory_tags.extend(mandatory_tag)

    def add_to_active_tags(self, new_active_tag, weight):
        """This function prevents duplicate tags in the active_tags list and adds weights if a duplicate exists.
        The new_active_tag argument is a Tag object, not an active_tag object! This function is meant to create active_tag objects."""
        match = len([active_tag for active_tag in self.active_tags if active_tag.tag == new_active_tag]) > 0
        if match: # The tag already exists in the active_tags list and must be added to.
            for i, active_tag in enumerate(self.active_tags):
                if active_tag.tag == new_active_tag:
                    self.active_tags[i] = self.active_tag(new_active_tag, self.active_tags[i].weight + weight)
        else: # The tag must be newly added to the active_tags list.
            self.active_tags.append(self.active_tag(new_active_tag, weight))

    def update_active_tags(self):
        """Creates a list of all current active tags, the forbidden tags and the mandatory tags."""
        self.active_tags = []
        # for question_with_answers in self.questionnaire:
        #     for option_with_selection in question_with_answers.options_with_selection:
        #         if option_with_selection.selected:
        #             # This option is enabled, we want the associated tags.
        #             for option_tag in option_with_selection.option.tags:
        #                 self.add_to_active_tags(option_tag, question_with_answers.weight)
        for question in self.worksession.question_set.questions:
            for option in question.options:
                if self.worksession.is_option_selected(option):
                    for option_tag in option.tags:
                        self.add_to_active_tags(option_tag, self.worksession.get_weight(question))

    def is_instrument_in_scope(self, instrument):
        """ Instruments are not in scope if they contain a forbidden tag (for this tool),
        or if they do not contain a mandatory tag (for this tool). """
        for forbidden_tag in self.forbidden_tags: # None of the tags may be in the forbidden list.
             if len([tag.tag for tag in instrument.tags if tag.tag == forbidden_tag]) > 0:
                return False
        for mandatory_tag in self.mandatory_tags: # At least one of the mandatory tags should be present.
            if len([tag.tag for tag in instrument.tags if tag.tag == mandatory_tag]) == 0:
                return False
        return True
                 

    def calculate_score(self, instrument):
        # First apply the question set tag constraints:
        score = 0
        multiplier = 1
        for forbidden_tag in self.forbidden_tags: # None of the tags may be in the forbidden list.
             if len([tag.tag for tag in instrument.tags if tag.tag == forbidden_tag]) > 0:
                return 0
        for mandatory_tag in self.mandatory_tags: # At least one of the mandatory tags should be present.
            if len([tag.tag for tag in instrument.tags if tag.tag == mandatory_tag]) == 0:
                return 0
        # Then calculate score based on options:
        for active_tag in self.active_tags:
            for tag_assignment in instrument.tags:
                if tag_assignment.tag == active_tag.tag:
                    score += (tag_assignment.weight * active_tag.weight)
                    multiplier *= tag_assignment.multiplier
        # The multiplier is applied last. This choice ensures that instruments with any 0-multiplier always get score=0.
        score *= multiplier
        return score
    
    def explain_score(self, instrument):
        """Deze functie geeft als resultaat een uitleg van de berekende score. Dit kan echt veel slimmer 
        als resultaat van calculate_score (hierboven)."""
        explanation = {}
        explanation['instrument_name'] = instrument.name
        explanation['instrument_id'] = instrument.id
        # First apply the question set tag constraints:
        score = 0
        multiplier = 1
            
        for forbidden_tag in self.forbidden_tags: # None of the tags may be in the forbidden list.
             if len([tag.tag for tag in instrument.tags if tag.tag == forbidden_tag]) > 0:
                explanation['forbidden_tags_found'] = ( len(self.forbidden_tags) > 0 )
                multiplier = 0
        for mandatory_tag in self.mandatory_tags: # At least one of the mandatory tags should be present.
            if len([tag.tag for tag in instrument.tags if tag.tag == mandatory_tag]) == 0:
                explanation['mandatory_tags_not_found'] = ( len(self.mandatory_tags) == 0 )
                multiplier = 0
        explanation['multiplier_after_worksession_tags'] = multiplier
        # Then calculate score based on options:
        enriched_tags = []
        for active_tag in self.active_tags:
            for tag_assignment in instrument.tags:
                if tag_assignment.tag == active_tag.tag:
                    score += (tag_assignment.weight * active_tag.weight)
                    enriched_tags.append( {'name':active_tag.tag.name, 
                                           'weight_in_instrument':tag_assignment.weight, 
                                           'weight_in_question':active_tag.weight,
                                           'contribution':tag_assignment.weight * active_tag.weight,
                                           'factor_in_instrument': tag_assignment.multiplier})
                    multiplier *= tag_assignment.multiplier
        explanation['tags'] = enriched_tags
        # The multiplier is applied last. This choice ensures that instruments with any 0-multiplier always get score=0.
        explanation['final_score'] = score
        explanation['final_multiplier'] = multiplier
        explanation['final'] = score * multiplier
        return explanation


    def update(self):
        self.update_active_tags()      
        self.scored_instruments = []
        for instrument in self.all_instruments:
            if self.is_instrument_in_scope(instrument):
                self.scored_instruments.append([instrument, self.calculate_score(instrument)])


    def debug_info(self):
        print('=== Debug info =====================================')
        print(f'Mandatory tags: {self.mandatory_tags}')
        print(f'Forbidden tags: {self.forbidden_tags}')
        print('Active tags:')
        for at in self.active_tags:
            print(f'  {at.tag.name} [W={at.weight}]')
        print('Scored instruments')
        for si in self.scored_instruments:
            print (f'  {si.instrument.name} [S={si.score}]')
        print('====================================================')


    def get_sorted_instruments(self):
        """Returns a sorted list of all instruments and their score."""
        self.update()
        return sorted(self.scored_instruments, key=itemgetter(1), reverse=True)


    def get_highest_score(self):
        """Returns the score of the highest scoring instrument."""
        self.update() #TODO er wordt te vaak geupdate, en dat is niet nodig.
        top_score = 0
        for instrument, score in self.scored_instruments:
            top_score = max(top_score, score)
        return top_score


    def get_best_instrument(self):
        """Returns the first item of the sorted list of all instruments and their score."""
        self.update()
        return sorted(self.scored_instruments, key=itemgetter(1), reverse=True)[0]

    
    def get_active_tags(self):
        self.update()
        return self.active_tags