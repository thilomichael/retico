"""
A simple n-gram dialogue manager
"""

import pickle
import random

from retico.dialogue.common import AbstractDialogueManager

N = 5


class NGramDialogueManager(AbstractDialogueManager):
    """A simple n-gram dialogue manager."""

    def __init__(self, model_file, name):
        thing = pickle.load(open(model_file, "rb"))
        self.map = thing["%s_map" % name]
        self.name = name
        if self.name == "caller":
            self.interlocutor = "callee"
        else:
            self.interlocutor = "caller"
        self.dialogue_finished = False
        self.dialogue_log = []

    def process_act(self, act, concepts):
        if concepts.keys():
            act_str = "%s:%s" % (act, ",".join(concepts.keys()))
        else:
            act_str = act
        self.dialogue_log.append("%s@%s" % (act_str, self.interlocutor))

    def _create_ngram(self, n):
        last_n = self.dialogue_log[-n:] # Get last N from log
        n_gram = ";".join(last_n)
        if not self.map.get(n_gram) and n > 1:
            n_gram = self._create_ngram(n-1)
        return n_gram

    def _get_random(self, act):
        total = 0
        for value in self.map[act].values():
            total += value
        random_choice = random.uniform(0, total)
        for key, value in self.map[act].items():
            random_choice -= value
            if random_choice < 0:
                return key
        assert False, "This should not happen"

    def next_act(self):
        n_gram = self._create_ngram(N)
        if not self.map.get(n_gram):
            print("COULD NOT FIND NGRAM %s" % n_gram)
            return "stalling", {}

        chosen_act = self._get_random(n_gram)
        self.dialogue_log.append("%s@%s" % (chosen_act, self.name))
        if "goodbye" in chosen_act:
            self.dialogue_finished = True
        ca_split = chosen_act.split(":")
        act = ca_split[0]
        concepts = {}
        if len(ca_split) > 1:
            for thing in ca_split[1].split(","):
                concepts[thing] = ""
        return act, concepts
        # return chosen_act, self._determine_keep(chosen_act)
