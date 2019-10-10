"""A Module for the dialogue management in the conversation simulation.

The main class in this module is the `TurnTakingDialogueManagerModule` that keeps
track of the state of the interlocutor and its own actions to model realistic
turn taking.
This module is dialogue manager agnostic and in itself does not utilize any
dialogue manager in particular. It expects dialogue managers that conform to the
interface defined by `retico.dialogue.common.AbstractDialogueManager`.

Additionally there are wrapper classes that insert the dialogue managers
implemented in `retico.dialogue.manager` into the TurnTakingDialogueManager.

The current dialogue managers are:
    AgendaDialogueManagerModule: A module that uses a generic agenda based
        dialogue manager defined in `retico.dialogue.manager.agenda`.
    NGramDialogueManagerModule: A module that uses a simple ngram model that is
        defined in `retico.dialogue.manager.ngram`.

There are dialogue managers that depend on third party packages that are moved
to their own python-modules so that importing is made easier when those packages
are not installed:
    RasaDialogueManagerModule (in `dm_rasa.py`): A dialogue manager based on the
        rasa core package. This is a dialogue manager from the rasa.ai project
        that utilizes a recurrent neural network approach to predict actions.
    ConvSimDialogueManagerModule (in `dm_convsim.py`): A dialogue manager based
        on the convsim project that uses an agenda based dialogue manager that
        also includes speech output and turn information. The turn information
        is not used in this environment (because the turn taking is managed by
        the TurnTakingDialogueManagerModule).
"""

import time
import threading
import random
import math

from retico.core import abstract
from retico.core.dialogue.common import DialogueActIU, DispatchableActIU
from retico.core.audio.common import DispatchedAudioIU
from retico.core.prosody.common import EndOfTurnIU
from retico.dialogue.manager.agenda import AgendaDialogueManager
from retico.dialogue.manager.ngram import NGramDialogueManager


class DialogueState:
    """A Class that represents the state of a dialogue partner. Each dialogue
    manager should have two dialogue states that keep track of the taking and
    dialogue act information of themself and their interlocutor.
    """

    def __init__(self):
        """Create a new DialogueState with the default parameters

        Returns:
            type: Description of returned object.

        """
        self.utter_start = 0.0
        self.utter_end = 0.0
        self.dialogue_started = False
        self.is_speaking = False
        self.completion = 0.0
        self.current_act = None
        self.last_act = None

    def __repr__(self):
        rep = ""
        rep += "utter_start: %f\n" % self.utter_start
        rep += "utter_end: %f\n" % self.utter_end
        rep += "dialogue_started: %s\n" % self.dialogue_started
        rep += "is_speaking: %s\n" % self.is_speaking
        rep += "completion: %s\n" % self.completion
        rep += "current_act: %s\n" % self.current_act
        rep += "last_act: %s\n" % self.last_act
        return rep

    @property
    def ts_utter_start(self):
        """Return the time since the current utterance started.

        Returns:
            flaot: The time since the current utterance started.

        """
        return time.time() - self.utter_start

    @property
    def ts_utter_end(self):
        """Return the time since the last utterance ended.

        Returns:
            float: The time since the last utterance ended.

        """
        return time.time() - self.utter_end

    @property
    def in_middle_of_turn(self):
        """Returns whether the agent is in the "middle" of a turn. This is
        determined by the expected completion (from the eot module) or the
        completion of the AudioDispatcherModule.

        An agent is in the "middle" of a turn when their completion rate is
        between 0.3 and 0.7.

        Returns:
            bool: Whether the agent is in the middle of their turn.

        """
        return self.completion > 0.3 and self.completion < 0.7


# ==============================================================================


class TurnTakingDialogueManagerModule(abstract.AbstractModule):
    """An incremental Dialogue Manager Module that wraps a normal Dialogue
    Manager and extends it by the concept of turn taking.

    This module needs three inputs:
        - DialogueActIUs that represent the semantic information the
            interlocutor is saying.
        - EndOfTurnIUs that give an estimate on when the utterance of the
            interlocutor ends.
        - DispatchedAudioIUs that give feedback on how far the agents own
            utterance has progressed.

    The TurnTakingDialogueManager module in itself does not contain a dialogue
    manager that would be accessible via the property "dialogue_manager". Thus,
    to use this module, a new class has to be created inheriting from this class
    that sets the dialogue_manager and initializes it accordingly.

    Attributes:
        first_utterance (bool): Whether the agent is the first one to talk
        dialogue_finished (bool): Whether or not the dialogue is finished
            (usually set by the `stop()` method to end the dialogue thread)
        dialogue_started (bool): Whether or not the dialogue has started.
        dialogue_manager (retico.dialogue.common.AbstractDialogueManager):
            A dialogue manager that in this implementation is not set
            automatically. This may either be set after initialization or a
            class should inherit from this class.
        me (DialogueState): The dialogue state of this agent.
        other (DialogueState): The dialogue state of the interlocutor.
        suspended (bool): Whether or not the dialogue_loop is currently
            suspended
        rnd (float): A uniformly distributed random number between 0 and 1 that
            is used to in the gap, overlap and pauses models.
    """

    SLEEP_TIME = 0.05
    """The time to sleep between dialogue state checks. This is not necessary
    but helps decreasing the load."""
    P_PROCESS = 0.30
    """The threshold of EoT prediction value that triggers the processing of the
    next dialogue act."""

    EVENT_DIALOGUE_ENDED = "dialogue_end"
    """Name of the event that gets called when the agent dispatches `goodbye`"""
    EVENT_SAID = "said"
    """Name of the event that gets called when the agent dispatches a dialogue
    act. Thie called event includes a parameter `iu` is the produced
    DispatchableActIU."""
    EVENT_SILENCE = "silence"
    """The name of the event that gets called when the agents silences
    itself."""
    EVENT_HEARD = "heard"
    """The name of the event that gets called when the agent receives a
    DialogueAct from the User."""
    EVENT_DOUBLE_TALK = "doubeltalk"
    """The name of the event that gets called when a double talk interruption
    is detected and the agent silences itself to not be rude."""

    @staticmethod
    def name():
        return "Turn Taking DM Module"

    @staticmethod
    def description():
        return "A dialogue manager that uses eot predictions for turn taking"

    @staticmethod
    def input_ius():
        return [DialogueActIU, DispatchedAudioIU, EndOfTurnIU]

    @staticmethod
    def output_iu():
        return DispatchableActIU

    def __init__(self, first_utterance=True, **kwargs):
        """Initializes the class with the flag of wether the agent should start
        the conversation or wait until the interlocutor starts the conversation.

        Args:
            first_utterance (bool): Whether this agent starts the conversation
        """
        super().__init__(**kwargs)
        self.first_utterance = first_utterance
        self.dialogue_finished = False
        self.dialogue_started = False
        self.dialogue_manager = None

        self.me = DialogueState()
        self.other = DialogueState()

        self.suspended = False
        self.rnd = 0
        self.reset_random()

    def reset_random(self):
        """Resets the internal random variable to a new random value between 0
        and 1.

        The internal random variable is used to determine whether and when the
        the interlocutor should be interrupted or when the agent should continue
        speaking after they made a pause.
        """
        self.rnd = random.random()
        while self.rnd == 0:
            self.rnd = random.random()

    def time_since_eot(self):
        """Returns the seconds that have passed since the interlocutor finished
        their utterance. If the interlocutor is still speaking, a negative float
        is returned, representing the estimation of seconds to go until the
        interlocutor will end their turn.

        Returns:
            float: The time in second since the interlocutors end of turn (might
                be negative when the interlocutor is still talking)
        """
        if self.other.is_speaking:
            utter_len = self.other.ts_utter_start
            eot_pred = self.other.completion
            if eot_pred == 0:
                eot_pred = 0.000001
            x = (utter_len * (1 / eot_pred)) - utter_len
            return -x  # Return negative, because 0 is the end of the utterance
        return self.other.ts_utter_end

    @property
    def role(self):
        """Returns the role (caller or callee) of this dialogue manager. This
        is determined by the first_utterance attribute.

        Returns:
            str: "caller" or "callee"

        """
        if self.first_utterance:
            return "callee"
        return "caller"

    @property
    def both_speak(self):
        """Whether both agents are currently speaking

        Returns:
            bool: Whether both agents are currently speaking
        """
        return self.me.is_speaking and self.other.is_speaking

    @property
    def both_silent(self):
        """Whether both agents are currently not speaking

        Returns:
            bool: Whether both agents are currently not speaking
        """
        return not self.me.is_speaking and not self.other.is_speaking

    @property
    def i_speak(self):
        """Whether this agent is speaking and the interlocutor is silent

        Returns:
            bool: Whether this agent is speaking and the interlocutor is silent
        """
        return self.me.is_speaking and not self.other.is_speaking

    @property
    def they_speak(self):
        """Whether the interlocutor is speaking and this agent is silent

        Returns:
            bool: Whether the interlocutor is speaking and this agent is silent
        """
        return not self.me.is_speaking and self.other.is_speaking

    def reset_utterance_timers(self):
        """Reset the timers for self and the interlocutor.

        This method is used in the begining of the dialogue to avoid strange
        behavior when no utterance has preceeded.
        """
        now = time.time()
        self.me.utter_start = now
        self.me.utter_end = now
        self.other.utter_start = now
        self.other.utter_end = now

    def handle_dilaogue_act(self, input_iu):
        """Set the current act of the interlocutor.

        If the EoT prediction of the interlocutors current dialogue utterance
        is greater than P_PROCESS, the act and the concepts are processewd over
        by the dialogue manager and thus the state of the DM is updated.

        Args:
            input_iu (IncrementalUnit): The dialogue act incremental unit from
                the interlocutor.
        """
        incoming_str = self._create_act_string(input_iu.act, input_iu.concepts)
        oca = self.other.current_act
        current_str = "None:None"
        if oca is not None:
            current_str = self._create_act_string(oca.act, oca.concepts)
        if self.other.completion > self.P_PROCESS:
            if incoming_str != current_str:
                self.other.current_act = input_iu
                self.dialogue_manager.process_act(input_iu.act, input_iu.concepts)
                self.event_call(self.EVENT_HEARD, {"iu": input_iu})
        self.dialogue_started = True

    def handle_dispatched_audio(self, input_iu):
        """Handles the state of the agents own dispatched audio.

        This method sets the utter_end and utter_start flag of the DialogueState
        object that corresponds to its own state.
        After an IU is recieved that changes the iterlocutor own state (to
        speaking or silent), the suspend flag is set to False so that the
        dialogue loop may continue handling the current dialogue state.

        This method choses a new random number when it detects that the agent
        has started to speak.

        Args:
            input_iu (DispatchedAudioIU): The dispatched audio IU of the agents
                AudioDispatcherModule.
        """
        if self.me.is_speaking and not input_iu.is_dispatching:
            self.me.utter_end = time.time()
            self.me.last_act = self.me.current_act
            self.me.current_act = None
            self.suspended = False
        elif not self.me.is_speaking and input_iu.is_dispatching:
            self.me.utter_start = time.time()
            self.suspended = False
            self.reset_random()
        self.me.is_speaking = input_iu.is_dispatching
        self.me.completion = input_iu.completion

    def handle_eot(self, input_iu):
        """Handles the state of the agents interlocutors utterances.

        This method sets the utter_end and utter_start flag of the DialogueState
        object that corresponds to the interlocutors state.

        This method choses a new random number when it detects that the
        interlocutor has started to speak

        Args:
            input_iu (EndOfTurnIU): The end of turn prediction of the agents
                interlocutor.
        """
        if self.other.is_speaking and not input_iu.is_speaking:
            self.other.utter_end = time.time()
        elif not self.other.is_speaking and input_iu.is_speaking:
            self.other.utter_start = time.time()
            self.reset_random()
        self.other.is_speaking = input_iu.is_speaking
        self.other.completion = input_iu.probability
        if self.other.completion == 1.0:
            self.other.last_act = self.other.current_act
            self.other.current_act = None

    def process_iu(self, input_iu):
        """Processes the incoming Dialogue Act and EoT predictions of the
        interloctor and also the dispatching progress of its own
        AudioDispatcherModule.

        Args:
            input_iu (IncrementalUnit): An incremental unit that may be of type
                DialogueActIU, DispatchedAudioIU or EndOfTurnIU.

        Returns:
            None: Returns always None because IUs are produced asynchronously.
        """
        # First, we switch between the different types of IUs
        if isinstance(input_iu, DialogueActIU):
            self.handle_dilaogue_act(input_iu)
        elif isinstance(input_iu, DispatchedAudioIU):
            self.handle_dispatched_audio(input_iu)
        elif isinstance(input_iu, EndOfTurnIU):
            self.handle_eot(input_iu)
        return None

    @staticmethod
    def _create_act_string(act, concepts):
        """Takes the act and concepts of the dialogue manager and creates a new
        unique string from it in the form of:
            act:concept1,concept2,concept3
        While the concepts argument expects a dict mapping from concept names to
        their value, the string representation only uses keys to create the
        unique string.

        Args:
            act (str): A string representing the act (intent) that should be
                encoded.
            concepts (dict): A dictionary mapping concept names to their values.

        Returns:
            str: A string representaiton of the act-concept-pair.

        """
        if concepts.keys():
            return "%s:%s" % (act, ",".join(concepts.keys()))
        return act

    def dispatch_act(self, act, concepts):
        """Takes an act and a dict of concepts, creates a new DialogueActIU with
        the dispatch-flag set to True and appends it to the right_buffer of the
        module.

        It additionally sets the "message_data" meta field of the DialogueActIU.

        If the agent should stop speaking, the `silence()` function may be used.

        Args:
            act (str): A string representing the act (intent)
            concepts (dict): A dictionary mapping concept names to their values.

        Returns:
            type: Description of returned object.

        """
        meta_act = self._create_act_string(act, concepts)
        output_iu = self.create_iu(None)
        output_iu.set_act(act, concepts)
        output_iu.meta_data["message_data"] = meta_act
        output_iu.dispatch = True
        self.me.last_act = self.me.current_act
        self.me.current_act = output_iu
        self.append(output_iu)
        return output_iu

    def speak(self):
        """Retrieve the next dialogue act from the dialogue manager and dispatch
        it immediately. This method calls the event `EVENT_SAID` with the
        created IU as the parameter `iu`.

        If the act that the dialogue manager created is "goodbye" it calls the
        event `EVENT_DIALOGUE_ENDED`.
        """
        act, concepts = self.dialogue_manager.next_act()
        iu = self.dispatch_act(act, concepts)
        self.event_call(self.EVENT_SAID, data={"iu": iu})
        if act == "goodbye":
            self.event_call(self.EVENT_DIALOGUE_ENDED)
        self.suspended = True

    def silence(self):
        """Silence the current utterance of the agent. For this, a new
        DialogueActIU is created with the dispatch-flag set to False.

        This method calls the event `EVENT_SILENCE` and suspends the dialog
        loop."""
        output_iu = self.create_iu(None)
        output_iu.set_act("", {})
        output_iu.dispatch = False
        self.append(output_iu)
        self.event_call(self.EVENT_SILENCE)
        self.suspended = True

    def i_spoke_last(self):
        """Determines whether or not the agent was the last one to speak. If the
        agent is currently speaking (so also when double talk is occuring) it
        returns True.

        Returns:
            bool: Whether the agent was the last one to speak.
        """
        if self.me.is_speaking:
            return True
        elif self.other.is_speaking:
            return False
        return self.me.utter_end > self.other.utter_end

    def gando_model(self):
        """The model that uses the current random number `rnd` (uniformly
        distributed between 0 and 1) to model gaps and overlaps.

        Based on the method of [Lunsford et al. 2016], the gaps and overlaps of
        the underlying conversation (SCT and RNV) were calculated. The
        cumulative sum of gaps and overlaps at a specific time dt away from the
        end of turn (t_end_of_interl_turn - t_beginning_of_own_turn) was
        approximated using logistic regression. The resulting function was then
        inverted resulting in a model taking in a random value from 0 to 1 and
        predicting when (realtive to the end of the interlocutors turn) the next
        turn should begin.

        A negative value will result in an overlap (there, an EoT prediction can
        be used to calculated the predicted remaining duration of the current
        utterance). A positive value will result in a gap.


        Returns:
            float: Time relative to the interlocutors (predicted) end of turn in
                seconds.

        """
        result = -0.322581 * math.log(0.433008 * (-1 + 1 / self.rnd))  # GANDO SCT11
        # result = result - 0.5  # Hack to counter balance the unprecise TTS signal

        if self.other.current_act:
            if (
                self.other.current_act.act == "provide_partial"
                or self.other.current_act.act == "provide_info"
                or self.other.current_act.act == "confirm"
            ):  # Switch to GANDO Model of RNV when uttering provide_partial and provide_info
                result = -0.159767 * math.log(
                    0.169563 * (-1 + 1 / self.rnd)
                )  # GANDO RNV1
                if result > 0:
                    result *= 0.5

        return result

    def pause_model(self):
        """The model that uses the current random number `rnd` (uniformly
        distributed between 0 and 1) to model the pause between two utterances/
        dialogue acts/turns of the same agent.

        This model is based on the method of [Lunsford et al. 2016]. The
        cumulative sum of pauses at a specific time away from the end of the
        last utterance of the same speaker was approximated using logistic
        regression. The resulting function was then inverted resulting in a
        model taking in a random value from 0 to 1 and predicting when the
        speaker should continue speaking after their own turn.

        Returns:
            float: Time relative to end of last utterance in seconds.
        """
        val = 0.925071 * (0.843217 + 2.92309 * math.pow(self.rnd, 2))  # PAUSE SCT11
        # val = -0.161705 * math.log(0.00106779 * (-1 + 1/self.rnd)) # PAUSE RNV1
        # val = 0.0538261 * (14.9693 + 28.299 * math.pow(self.rnd, 2)) # PAUSE RNV1 sqrt
        # val = val - 0.5  # Hack to counter balance the unprecise TTS signal
        if self.me.last_act:
            if self.me.last_act.act == "request_info":
                val += 1.5
            if self.other.last_act:
                if (
                    self.me.last_act.act == "confirm"
                    and self.other.last_act.act == "provide_partial"
                ):
                    val += 0.5
                if (
                    self.other.last_act.act == "greeting"
                    and self.me.last_act.act == "greeting"
                ):
                    val = 0.2
            elif self.me.last_act.act == "greeting":
                val += 0.5
        if val < 0:  # This should never happen...?
            val = 0.2
        return val

    def should_interrupt(self):
        """Returns whether or not the agent should interrupt the interlocutor
        based on the gaps and overlaps (gando) model. If the predicted negative
        time until the interlocutors end of turn in seconds is greater than the
        modeled time, this method returns True.

        Generally the method returns false if the interlocutor did not speak for
        more than 1 second (to avoid akward intteruptions during short
        utterances).

        Returns:
            bool: Whether the agent should interrupt the interlocutor.

        """
        if self.other.ts_utter_start < 1:
            return False
        return self.time_since_eot() > self.gando_model()

    def should_speak(self):
        """Returns whether or not the agent should speak after the interlocutor
        stopped speaking. This is determined by the gaps and overlaps (gando)
        model.

        Returns:
            bool: Whether the agent should take the turn from the interlocutor.
        """
        return self.time_since_eot() > self.gando_model()

    def should_continue(self):
        """Returns whether or not the agent should continue speaking after they
        made a pause (between two utterances/dialogue acts).

        Returns:
            bool: Whether the agent continue speaking.
        """
        return self.me.ts_utter_end > self.pause_model()

    def double_talk_detected(self):
        """Returns whether or not double talk was detected.

        Double talk is only detected when both the agent and the interlocutor
        are speaking and also if they are both in the middle of the turn
        (not at the beginning or the end, because then it would be a normal
        overlap).

        Returns:
            bool: Whether or not double talk was detected.
        """
        return self.me.in_middle_of_turn or self.other.in_middle_of_turn

    def dialogue_loop(self):
        """The dialogue loop that continuously checks the state of the agent and
        the interlocutor to determine what action to perform next.

        The dialogue loop is suspended when the agent starts speaking until the
        agent recieves DispatchedAudioIU from itself and registeres that the
        speech is being produced.

        During the loop, the agent checks the spaking states of both themself
        and their interlocutor to determin whether or not they should interrupt,
        take over the turn, continue their own turn or prevent double talk.

        When two agents are interacting the pause-model of the one agent and the
        gando-model of the other agent determine if a turn is passed over or if
        the agent continues speaking.
        """
        while not self.dialogue_finished:

            # Suspend execution until something happens
            while self.suspended:
                time.sleep(self.SLEEP_TIME)

            if not self.dialogue_started:
                if self.first_utterance:
                    self.reset_utterance_timers()
                    self.speak()
                    self.dialogue_started = True
                continue

            if self.i_speak:
                pass  # Do nothing.
            elif self.they_speak:
                if self.should_interrupt():
                    self.speak()
            elif self.both_silent:
                if not self.i_spoke_last() and self.should_speak():
                    self.speak()
                elif self.i_spoke_last() and self.should_continue():
                    self.speak()
            elif self.both_speak:
                if self.double_talk_detected():
                    if random.random() < 0.1:
                        self.event_call(
                            self.EVENT_DOUBLE_TALK,
                            {
                                "my_iu": self.me.current_act,
                                "other_iu": self.other.current_act,
                            },
                        )
                        self.silence()

            time.sleep(self.SLEEP_TIME)

    def setup(self):
        """Sets the dialogue_finished flag to false. This may be overwritten
        by a class to setup the dialogue manager."""
        self.dialogue_finished = False

    def prepare_run(self):
        """Prepares the dialogue_loop and the DialogueState of the agent and the
        interlocutor by resetting the timers.
        This method starts the dialogue_loop."""
        self.reset_utterance_timers()
        t = threading.Thread(target=self.dialogue_loop)
        t.start()

    def shutdown(self):
        """Sets the dialogue_finished flag that eventually terminates the
        dialogue_loop."""
        self.dialogue_finished = True

    def __repr__(self):
        return super().__repr__() + " " + self.role


# ==============================================================================


class AgendaDialogueManagerModule(TurnTakingDialogueManagerModule):
    """A turn taking dialogue manager module that utilizes the agenda based
    dialogue manager implemented in `retico.dialogue.manager.agenda` to generate
    a consisten dialogue.

    As the dialogue manager is agenda based it takes an agenda_file in form of
    an .ini config file. It also utilizes an "available act" file, that
    restricts the dialogue acts that the DM may produce.
    """

    @staticmethod
    def name():
        return "Agenda DM Module"

    def __init__(self, agenda_file, aa_file, first_utterance, **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.agenda_file = agenda_file
        self.aa_file = aa_file
        self.first_utterance = first_utterance

    def setup(self):
        super().setup()
        self.dialogue_manager = AgendaDialogueManager(
            self.aa_file, self.agenda_file, self.first_utterance
        )


class NGramDialogueManagerModule(TurnTakingDialogueManagerModule):
    """A turn taking dialogue manager module that utilizes the n-gram based
    dialogue manager implemented in `retico.dialogue.manager.ngram` to generate
    dialogue acts.

    This approach works not that well but does the job.
    """

    @staticmethod
    def name():
        return "N-Gram DM Module"

    def __init__(self, ngram_model, first_utterance, **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.ngram_model = ngram_model
        self.first_utterance = first_utterance

    def setup(self):
        super().setup()
        if self.first_utterance:
            self.dialogue_manager = NGramDialogueManager(self.ngram_model, "callee")
        else:
            self.dialogue_manager = NGramDialogueManager(self.ngram_model, "caller")
