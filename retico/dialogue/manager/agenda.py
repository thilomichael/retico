"""
An agenda based dialogue manager that uses a stack structure only for immediate
answers to questions and otherwise decides the next dialogue act based on the
state of the agenda.

This dialogue manager also incorporates an ActGuider that looks at real life
data and tries to suggest dialogue acts that were already seen in the data
rather than completely 'artifical' ones.

The dialogue manager is modeled after the agenda-based user simulator described
in [Schatzmann et al., 2007] but adds the additional features of "act guidance"
and "field mentioning" to allows for a correct behaviour during dialogues that
incorporate dynamic turn taking.

The rules of the agenda-based dialogue manager are as follows:
    GREETING: Greet and check off potentially mentioned field (such as the
        interlocutors name)
    GOODBYE: Say goodbye
    PROVIDE_INFO: confirm and check off the information that was provided.
    PROVIDE_PARTIAL: confirm and check off the partial bit of information that
        was provided.
    REQUEST_INFO: provide the requested information regardless of the state of
        that field and check off that information
    OFFER_INFO: provide that information and mark it as checked.
    STALLING: do nothing
    REQUEST_CONFIRM: confirm the field that was requested
    CONFIRM: mark the field as confirmed
    MISUNDERSTANDING: repeat the field
    THANKS: utter welcome
    WELCOME: do nothing

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
        """Initialize the Agenda

        Args:
            agendafile (str): Path to the ini-file to load.
        """
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(agendafile)
        if not self.config:
            raise FileNotFoundError("Could not find '%s' or it is empty!")

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
        """Returns whether or not the given field is a partial of this argenda
        or not.

        Args:
            field_name (str): The name of a field (without a partial number
                added to it).

        Returns:
            bool: Whether or not that field is a partial.

        """
        return bool(self.fields.get(field_name + "-0"))

    def has_field(self, field_name):
        """Return whether or not the given field name is a field of the current
        agenda.

        Args:
            field_name (str): Name of the field to test for.

        Returns:
            bool: Whether the field name is part of the agenda.

        """
        return bool(self.fields.get(field_name))

    def mention_field(self, field_name):
        """Sets the field's mentioned flag to True.

        If the field is not part of the agenda, this method just does nothing.

        Args:
            field_name(str): Name of the filed
        """
        if self.fields.get(field_name):
            self.fields[field_name].mentioned = True

    def confirm_field(self, field_name):
        """Sets teh field's confirm flag to True.

        If the field is not part of the agenda, this method just does nothing.

        Args:
            field_name(str): Name of the field
        """
        if self.fields.get(field_name):
            self.fields[field_name].confirmed = True

    def next_field(self):
        """
        Returns the next field (i.e. the first field that wasn't mentioned
        yet.)

        Depending on if a field is a request (`TYPE_REQ`) or a constraints
        (`TYPE_CON`), a field is considered the next field if it was not yet
        confirmed (for requests) or if it was not yet mentioned (for
        constraints).

        Returns:
            Field: The current field of the agenda.
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

    DA_FALLBACK = "stalling"

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

    def guide_utterance(self, act, entities, agenda):
        """Magic code that guides the utterance to conform to the underlying
        data.

        Args:
            act (str): The act that should be uttered
            entities (dict): The concepts that should be named

        Returns:
            (str,dict): A pair of a dialogue act and a dict of entities
            containing the "guided" act.

        """
        # TODO: Refactor this!
        if isinstance(entities, str):
            entities = {entities: ""}
        if isinstance(entities, dict):
            entities = list(entities.keys())
        entities_string = ",".join(entities)

        # If the dialogue act is not at all in the available acts, "stalling" is
        # the fallback
        if not self.guide.get(act):
            print("COULD NOT FIND", act)
            return self.DA_FALLBACK, []

        # If there are no entities, we can just return the act.
        if not entities_string:
            return act, entities

        # Here comes the hacky part: we loop through all available acts that
        # have the first entity in them. If the act is provide_info or
        # provide_partial we try to select acts+entities where the entities have
        # not been confirmed yet.
        # This prevents provide_infos that include information mentioned waaay
        # earlier in the conversation.
        possible_u = []  # All acts+entities that contain the first entity
        best_u = []  # All act+entities that contain the first entity and are not
        # Yet confirmed
        for e in self.guide[act]:
            if entities[0] in e:
                good = True
                if act == "provide_info" or act == "provide_partial":
                    for ent in e.split(","):
                        if agenda.has_field(ent) and agenda.fields[ent].confirmed:
                            good = False
                            break
                if good:
                    best_u.append((act, e.split(",")))
                possible_u.append((act, e.split(",")))
        # If we have acts+entites in best_u, we chose from there!
        if best_u:
            possible_u = best_u

        if possible_u:
            if "-" in entities[-1]:  # Evil hack for partials
                # We have a problem
                partial_int = int(entities[-1].split("-")[1])
                return_them = []
                for a, es in possible_u:
                    not_good = False
                    for e in es:
                        if act == "confirm":
                            if int(e.split("-")[1]) > partial_int:
                                not_good = True
                        if act == "provide_partial":
                            if int(e.split("-")[1]) < partial_int:
                                not_good = True
                    if not_good:
                        continue
                    return_them.append((a, es))
                if len(return_them) > 0:
                    a, es = random.choice(return_them)
                    if len(es) == 1:
                        a, es = random.choice(return_them)
                    return a, es
                if act == "provide_partial":
                    return random.choice(possible_u)
                if act == "confirm":
                    return "confirm", []
            else:
                return random.choice(possible_u)

        # If we see the exact act + entity combination in the provided list, we
        # can just return it!
        if entities_string in self.guide[act]:
            return act, entities

        if entities[-1] in self.guide[act]:
            return act, [entities[-1]]

        if "" in self.guide[act]:
            return act, []

        if act == "provide_info" and "-" in entities[-1]:
            return self.guide_utterance("provide_partial", entities, agenda)

        if act == "offer_info":
            for e in self.guide["provide_partial"]:
                if entities[0] + "-0" in e or entities[0] in e:
                    return "provide_partial", e.split(",")
            return self.guide_utterance("provide_info", entities, agenda)

        if act == "request_info" and entities == ["callee_name"]:
            return "greeting", []

        print("RETURN STALLING BECAUSE WE DONT HAVE", act, entities)
        return "stalling", []  # Instead of throwing an error, we just stall
        assert False, "Could not find utterance for %s - %s" % (act, entities)


class AgendaDialogueManager(AbstractDialogueManager):
    """
    An agenda based dialogue manager that is based on the agenda-based dialogue
    manager described in [Schatzmann et al. 2007], however it is improved in a
    way that constraints and requests may be just mentioned or be confirmed by
    the interlocutor or the dialogue manager itself.

    This allows for an arbitraty dialogue flow (in terms of turns) where each
    produced dialogue act is consistent with the agenda and the already obtained
    information, regardless of whether the interlocutor uttered something
    between the two acts.
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
        if random.random() < 0.23:
            return self.DA_REQUEST_CONFIRM, entities
        return self.DA_CONFIRM, entities

    def _rule_PROVIDE_PARTIAL(self, entities):
        if entities and "-" in entities[0]:
            self.agenda.confirm_field(entities[0].split("-")[0])
        return self.DA_CONFIRM, entities

    def _rule_REQUEST_INFO(self, entities):
        if entities and self.agenda.is_partial(entities[0]):
            return self.DA_PROVIDE_PARTIAL, entities[0] + "-0"
        return self.DA_PROVIDE_INFO, entities

    def _rule_OFFER_INFO(self, entities):
        return self.DA_CONFIRM, []

    def _rule_STALLING(self, entities):
        return None, None

    def _rule_REQUEST_CONFIRM(self, entities):
        return self.DA_CONFIRM, entities

    def _rule_CONFIRM(self, entities):
        if self.provided_entities:
            for e in self.provided_entities:
                self.agenda.confirm_field(e)
        return None, None

    def _rule_MISUNDERSTANDING(self, entities):
        if entities:
            return self.PROVIDE_INFO, entities
        return None, None

    def _rule_THANKS(self, entities):
        self.thanked = True
        if random.random() < 0.06:
            return self.DA_GOODBYE, []
        return self.DA_WELCOME, []

    def _rule_WELCOME(self, entities):
        self.thanked = True
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
        DA_WELCOME: _rule_WELCOME,
    }
    """A dict containing the rules on how the dialogue manager should react to
    a given incoming dialogue act."""

    def __init__(self, aa_file, agenda_file, starts_dialogue=True):
        self.act_guider = ActGuider(aa_file)
        self.agenda = Agenda(agenda_file)
        self.stack = []
        self.starts_dialogue = starts_dialogue
        self.dialogue_started = False
        self.dialogue_finished = False
        self.provided_entities = None
        self.thanked = False

    def create_next_act(self):
        """
        Creates the next dialogue act. This dialogue act may not conform to a
        act-concepts-pair that is seen in real life data. That's why the output
        of this method has to be given to the ActGuider.

        This method implements the following rules:
            - If the dialogue hasn't started yet, the dialogue manager produces
                a "greeting" dialogue act.
            - If dialogue acts are on the stack, the dialogue manager returns
                them
            - If no dialogue acts are on the stack, the dialogue manager
                determines the next field in the agenda and either requests the
                information if the field is a request or offers the information
                if the field is a constraint.
            - If no dialogue acts are on the stack and the agenda is completed
                the method returns a "goodbye" dialogue act.

        Returns:
            (str, dict): An act-concepts-pair that corresponds to the next act
            the dialogue manager has decided on.
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
            act, entities = self.stack.pop(0)
            if entities:
                ent = entities[0]
                while self.agenda.has_field(ent) and self.agenda.fields[ent].confirmed:
                    if not self.stack:
                        break
                    act, entities = self.stack.pop(0)
                    if not entities:
                        break
                    ent = entities[0]
            return act, entities

        current_field = self.agenda.next_field()
        if not current_field:
            if random.random() < 0.02:
                self.thanked = True
            if not self.thanked:
                self.thanked = True
                return self.DA_THANKS, []
            self.dialogue_finished = True
            return self.DA_GOODBYE, []
        if current_field.type == Field.TYPE_CON:
            if current_field.is_partial:
                if current_field.name[-1] == 0 and random.random() > 0.5:
                    return self.DA_OFFER_INFO, [current_field.name.split("-")[0]]
                return self.DA_PROVIDE_PARTIAL, [current_field.name]
            return self.DA_OFFER_INFO, [current_field.name]
        if current_field.type == Field.TYPE_REQ:
            return self.DA_REQUEST_INFO, [current_field.name]

    def next_act(self):
        act, entities = self.create_next_act()
        real_act, real_entities = self.act_guider.guide_utterance(
            act, entities, self.agenda
        )

        if real_act == "provide_info" or real_act == "provide_partial":
            self.provided_entities = real_entities
        else:
            self.provided_entities = None

        entity_dict = {}
        for entity in real_entities:
            self.agenda.mention_field(entity)
            entity_dict[entity] = ""
        if self.starts_dialogue:
            print("callee:", real_act, real_entities)
        else:
            print("caller:", real_act, real_entities)
        return real_act, entity_dict

    def push_to_stack(self, act, entities):
        """Pushes an act and entities to the stack.

        Args:
            act (str): The act that should be pushed to the stack.
            entities (dict): The entities corresponding to the act.
        """
        tup = (act, entities)
        if self.stack and self.stack[0][0] == self.DA_CONFIRM:
            self.stack.pop(0)
        if (act, entities) not in self.stack:
            self.stack.insert(0, tup)
        if random.random() < 0.07:
            self.stack.insert(0, (self.DA_STALLING, {}))

    def process_act(self, act, entities):
        """When processing an act this dialogue manager executes the rules
        according to the `RULES` dict and puts the resulting dialogue act and
        concepts onto the stack.

        Args:
            act (str): The act that should be processed.
            entities (dict): The entities that should be processed.
        """
        if isinstance(entities, dict):
            entities = list(entities.keys())
        for entity in entities:
            if (
                act == self.DA_PROVIDE_PARTIAL
                or act == self.DA_PROVIDE_INFO
                or act == self.DA_GREETING
            ):
                self.agenda.confirm_field(entity)
            self.agenda.mention_field(entity)

        ret_act, ret_entities = self.RULES[act](self, entities)
        if ret_act:
            self.push_to_stack(ret_act, ret_entities)
