"""
An agenda based dialogue manager that uses a stack structure only for immediate
answers to questions and otherwise decides the next dialogue act based on the
state of the agenda.

This dialogue manager also incorporates an ActGuider that looks at real life
data and tries to suggest dialogue acts that were already seen in the data
rather than completely 'artifical' ones.
"""

import configparser
import collections
import random

from retico.dialogue.common import AbstractDialogueManager


class Field:
    """
    One field in the agenda of the agenda-based agent. A field (a.k.a slot or
    entity) can be a constraint (TYPE_CON) if the field has a value (i.e. the
    agent wants to give that information to the interlocutor) or a request
    (TYPE_REQ) if the field has no value (i.e. the agent wants to request that
    information from the interlocutor).

    A field also has the two attributes mentioned (boolean) that denotes if the
    field was mentioned either by the agent or its interlocutor and the
    attribute confirmed (boolean) that denoes if the constraint/request of this
    field was explicitely confirmed in the conversation.

    If the type of field is request (TYPE_REQ) than the value will be None.
    """

    TYPE_CON = "constraint"
    TYPE_REQ = "request"

    def __init__(self, name, value):
        self.name = name
        if not value:
            self.value = None
        else:
            self.value = value
        if not value:
            self.type = self.TYPE_REQ
        else:
            self.type = self.TYPE_CON
        self.mentioned = False
        self.confirmed = False
        self.is_partial = "-" in name

class Agenda:
    """The agenda is read by an ini-file.

    For each section inside the ini-file, a section inside the agenda is
    created. Currently the sections are not used inside the dialogue management.

    The agenda can "check off" fields and returns the next appropriate field in
    the agenda (i.e. the next field that was not mentioned yet).
    """

    def __init__(self, agendafile):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(agendafile)

        self.agenda = collections.OrderedDict()
        self.fields = {}

        for section in self.config.sections():
            self.agenda[section] = []
            for field_name, value in self.config[section].items():
                if not value or not value.strip():
                    f = Field(field_name, None)
                    self.agenda[section].append(f)
                    self.fields[field_name] = f
                else:
                    partials = value.split("\n")
                    if len(partials) > 1:
                        for i, partial in enumerate(partials):
                            partial_name = "%s-%d" % (field_name, i)
                            f = Field(partial_name, partial)
                            self.agenda[section].append(f)
                            self.fields[partial_name] = f
                    else:
                        f = Field(field_name, value)
                        self.agenda[section].append(f)
                        self.fields[field_name] = f

    def print_agenda(self):
        """
        Prints the current agenda with all sections fields and their status.
        """
        for section in self.agenda:
            print("Section:", section)
            for field in self.agenda[section]:
                print("  Field:", field.name, "(", field.type, ")")
                print("    Mentioned:", field.mentioned)
                print("    Confirmed:", field.confirmed)

    def is_partial(self, field_name):
        return bool(self.fields.get(field_name+"-0"))

    def has_field(self, field_name):
        return bool(self.fields.get(field_name))

    def mention_field(self, field_name):
        """Sets the field's mentioned flag to True."""
        if self.fields.get(field_name):
            self.fields[field_name].mentioned = True

    def confirm_field(self, field_name):
        """Sets teh field's confirm flag to True."""
        if self.fields.get(field_name):
            self.fields[field_name].confirmed = True

    def next_field(self):
        """
        Returns the next field (i.e. the first field that wasn't mentioned
        yet.)
        """
        for section in self.agenda:
            for field in self.agenda[section]:
                if field.type == Field.TYPE_REQ and not field.confirmed:
                    return field
                elif field.type == Field.TYPE_CON and not field.mentioned:
                    return field
        return None


class ActGuider:
    """
    A class that uses a data-based approach to guiding dialogue acts.

    If a dialogue manager wants to utter an act with some entities the ActGuider
    looks if that combination of dialogue act and entities was previously found
    in the data basis. If not, it tries to suggest alterantive dialogue acts and
    entities that convey a similar meaning.
    """

    def __init__(self, aa_file):
        self.available_acts = []
        self.guide = {}
        with open(aa_file, "r") as f:
            for row in f:
                if len(row) < 2:  # Remove empty lines
                    continue
                self.available_acts.append(row[:-1])

        for utterance in self.available_acts:
            act_split = utterance.split(":")
            act = act_split[0]
            if not self.guide.get(act):
                self.guide[act] = []
            if len(act_split) > 1:
                self.guide[act].append(act_split[1])
            else:
                self.guide[act].append("")

    def guide_utterance(self, act, entities):
        """
        Magic code that guides the utterance to conform to the underlying data.
        """
        # TODO: Refactor this!
        entities_string = ",".join(entities)
        if not self.guide.get(act):
            return "stalling", []
        if entities_string in self.guide[act]:
            return act, entities
        if entities_string:
            possible_u = []
            for e in self.guide[act]:
                if entities[0] in e:
                    possible_u.append((act, e.split(",")))
            if possible_u:
                if "-" in entities[-1]:
                    # We have a problem
                    partial_int = int(entities[-1].split("-")[1])
                    for a, es in possible_u:
                        not_good = False
                        for e in es:
                            if int(e.split("-")[1]) > partial_int:
                                not_good = True
                        if not_good:
                            continue
                        return a, es
                else:
                    return random.choice(possible_u)
            if "" in self.guide[act]:
                return act, []
        if act == "offer_info":
            print("OFFER INFO FALLBACK")
            print(entities)
            for e in self.guide["provide_partial"]:
                if entities[0]+"-0" in e or entities[0] in e:
                    return "provide_partial", e.split(",")
            return self.guide_utterance("provide_info", entities)
        assert False, "Could not find utterance for %s - %s" % (act, entities)


class AgendaDialogueManager(AbstractDialogueManager):
    """
    An agenda based dialogue manager.
    """

    DA_GREETING = "greeting"
    DA_GOODBYE = "goodbye"
    DA_PROVIDE_INFO = "provide_info"
    DA_PROVIDE_PARTIAL = "provide_partial"
    DA_REQUEST_INFO = "request_info"
    DA_OFFER_INFO = "offer_info"
    DA_STALLING = "stalling"
    DA_REQUEST_CONFIRM = "request_confirm"
    DA_CONFIRM = "confirm"
    DA_MISUNDERSTANDING = "misunderstanding"
    DA_THANKS = "thanks"
    DA_WELCOME = "welcome"

    def _rule_GREETING(self, entities):
        return None, None

    def _rule_GOODBYE(self, entities):
        return None, None

    def _rule_PROVIDE_INFO(self, entities):
        return self.DA_CONFIRM, entities

    def _rule_PROVIDE_PARTIAL(self, entities):
        if entities and "-" in entities[0]:
            self.agenda.confirm_field(entities[0].split("-")[0])
        return self.DA_CONFIRM, entities

    def _rule_REQUEST_INFO(self, entities):
        if entities and self.agenda.is_partial(entities[0]):
            return self.DA_PROVIDE_PARTIAL, entities[0]+"-0"
        return self.DA_PROVIDE_INFO, entities

    def _rule_OFFER_INFO(self, entities):
        return self.CONFIRM, []

    def _rule_STALLING(self, entities):
        return None, None

    def _rule_REQUEST_CONFIRM(self, entities):
        return self.CONFIRM, entities

    def _rule_CONFIRM(self, entities):
        return None, None

    def _rule_MISUNDERSTANDING(self, entities):
        return self.PROVIDE_INFO, entities

    def _rule_THANKS(self, entities):
        return self.WELCOME, []

    def _rule_WELCOME(self, entities):
        return None, None

    RULES = {
        DA_GREETING: _rule_GREETING,
        DA_GOODBYE: _rule_GOODBYE,
        DA_PROVIDE_INFO: _rule_PROVIDE_INFO,
        DA_PROVIDE_PARTIAL: _rule_PROVIDE_PARTIAL,
        DA_REQUEST_INFO: _rule_REQUEST_INFO,
        DA_OFFER_INFO: _rule_OFFER_INFO,
        DA_STALLING: _rule_STALLING,
        DA_REQUEST_CONFIRM: _rule_REQUEST_CONFIRM,
        DA_CONFIRM: _rule_CONFIRM,
        DA_MISUNDERSTANDING: _rule_MISUNDERSTANDING,
        DA_THANKS: _rule_THANKS,
        DA_WELCOME: _rule_WELCOME
    }

    def __init__(self, aa_file, agenda_file, starts_dialogue=True):
        self.act_guider = ActGuider(aa_file)
        self.agenda = Agenda(agenda_file)
        self.stack = []
        self.starts_dialogue = starts_dialogue
        self.dialogue_started = False
        self.dialogue_finished = False

    def create_next_act(self):
        """
        Creates the next dialogue act. This dialogue act may not conform to a
        act-concepts-pair that is seen in real life data. That's why the output
        of this method has to be given to the ActGuider.
        """
        if not self.dialogue_started:
            self.dialogue_started = True
            # TODO:
            # Evil hack for mentioning the callee_name in the greeting
            # This will not work for agendas without the field "callee_name"
            # but won't break it either...
            if self.starts_dialogue and self.agenda.fields.get("callee_name"):
                self.agenda.mention_field("callee_name")
                return self.DA_GREETING, ["callee_name"]
            return self.DA_GREETING, []
        if self.stack:
            print(self.starts_dialogue, " -- pulled from stack")
            act, entities = self.stack.pop(0)
            return act, entities
        current_field = self.agenda.next_field()
        if not current_field:
            self.dialogue_finished = True
            return self.DA_GOODBYE, []
        if current_field.type == Field.TYPE_CON:
            if current_field.is_partial:
                return self.DA_PROVIDE_PARTIAL, [current_field.name]
            return self.DA_OFFER_INFO, [current_field.name]
        if current_field.type == Field.TYPE_REQ:
            return self.DA_REQUEST_INFO, [current_field.name]

    def next_act(self):
        act, entities = self.create_next_act()
        real_act, real_entities = self.act_guider.guide_utterance(act, entities)
        entity_dict = {}
        for entity in real_entities:
            print("mentioned ", entity)
            self.agenda.mention_field(entity)
            entity_dict[entity] = ""
        print(self.starts_dialogue, real_act, real_entities)
        return real_act, entity_dict

    def push_to_stack(self, act, entities):
        """Pushes an act and entities to the stack."""
        tup = (act, entities)
        if (act, entities) not in self.stack:
            # self.stack.insert(0, tup)
            self.stack.append(tup)

    def process_act(self, act, entities):
        if isinstance(entities, dict):
            entities = list(entities.keys())
        for entity in entities:
            if (act == self.DA_PROVIDE_PARTIAL or act == self.DA_PROVIDE_INFO or
                    act == self.DA_GREETING):
                self.agenda.confirm_field(entity)
            self.agenda.mention_field(entity)

        ret_act, ret_entities = self.RULES[act](self, entities)
        if ret_act:
            self.push_to_stack(ret_act, ret_entities)
