"""
A dialogue manager utilizing the rasa dialogue engine
"""

import json
import random

from retico.dialogue.common import AbstractDialogueManager

from rasa.core.agent import Agent
from rasa.core.policies.keras_policy import KerasPolicy


class RandomChoicePolicy(KerasPolicy):
    def predict_action_probabilities(self, tracker, domain):
        """This function activates the RNN to predict the next action, but then
        does a dice roll and sets the "winning" action to a probability of 100%"""
        predictions = super().predict_action_probabilities(tracker, domain)
        # print("PREDICTIONS", predictions[0])
        predictions[0] = 0

        total = sum(
            predictions
        )  # This is the sum of all predictions, should be close to 1
        new_predictions = [0.0] * len(
            predictions
        )  # This is the new predictions array. Initially all values are set to 0.0

        # This algorithm results in chosing each element in the array with the percentage it contains
        random_choice = random.uniform(
            0, total
        )  # Now we chose a number between 0 and 1
        for i, value in enumerate(
            predictions
        ):  # Go over every prediction of the real model
            random_choice -= (
                value
            )  # Substract the current prediction from our random number
            if random_choice < 0:  # If we hit 0, we take the element
                new_predictions[
                    i
                ] = 1.0  # Set the probability of that prediction to 100 %
                break

        # print(new_predictions)

        return new_predictions


def action_to_act(action):
    da_split = action.split(":")
    entities = {}
    if len(da_split) > 1:
        for entity in da_split[1].split(","):
            entities[entity] = "[empty]"
    return da_split[0], entities


def train():
    domain_file = "data/sct11/rasa_models/sct11_domain.yml"
    caller_model_path = "data/sct11/rasa_models/caller"
    callee_model_path = "data/sct11/rasa_models/callee"
    caller_training = "data/sct11/rasa_models/sct11_story_caller.md"
    callee_training = "data/sct11/rasa_models/sct11_story_callee.md"

    caller_agent = Agent(domain_file, policies=[RandomChoicePolicy()])
    callee_agent = Agent(domain_file, policies=[RandomChoicePolicy()])

    caller_train_data = caller_agent.load_data(caller_training)
    caller_agent.train(
        caller_train_data, epochs=100, batch_size=100, validation_split=0.2
    )
    caller_agent.persist(caller_model_path)

    callee_train_data = callee_agent.load_data(callee_training)
    callee_agent.train(
        callee_train_data, epochs=100, batch_size=100, validation_split=0.2
    )
    callee_agent.persist(callee_model_path)


class RasaDialogueManager(AbstractDialogueManager):
    def __init__(self, model_dir):
        self.agent = Agent.load(model_dir)
        self.acts = []
        self.dialogue_started = False

    def process_act(self, act, concepts):
        # if act == "stalling":
        #     return
        self.dialogue_started = True
        concept_string = json.dumps(concepts)
        rasa_msg = "/%s%s" % (act, concept_string)
        print("rasa_msg:", rasa_msg)
        results = self.agent.handle_message(rasa_msg)
        print("results:", results)
        self.acts.insert(0, results[0])

    def next_act(self):
        print("AVAILABLE ACTS:", len(self.acts))
        if not self.dialogue_started:
            self.dialogue_started = True
            return "greeting", {"callee_name": "[empty]"}
        if not self.acts:
            return "stalling", {}
        na = self.acts.pop(0)["text"]
        act, entities = action_to_act(na)
        print(act, " - ", entities)
        return act, entities


if __name__ == "__main__":
    train()
