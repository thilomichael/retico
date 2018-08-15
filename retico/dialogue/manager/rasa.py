"""
A dialogue manager utilizing the rasa dialogue engine
"""

import json
import random

from retico.dialogue.common import AbstractDialogueManager

from rasa_core.agent import Agent
from rasa_core.policies.keras_policy import  KerasPolicy

class RandomChoicePolicy(KerasPolicy):

    def predict_action_probabilities(self, tracker, domain):
        """This function activates the RNN to predict the next action, but then
        does a dice roll and sets the "winning" action to a probability of 100%"""
        predictions = super().predict_action_probabilities(tracker, domain)
        # print("PREDICTIONS", predictions)

        total = sum(predictions) # This is the sum of all predictions, should be close to 1
        new_predictions = [0.0] * len(predictions) # This is the new predictions array. Initially all values are set to 0.0

        # This algorithm results in chosing each element in the array with the percentage it contains
        random_choice = random.uniform(0, total) # Now we chose a number between 0 and 1
        for i, value in enumerate(predictions): # Go over every prediction of the real model
            random_choice -= value # Substract the current prediction from our random number
            if random_choice < 0: # If we hit 0, we take the element
                new_predictions[i] = 1.0 # Set the probability of that prediction to 100 %
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

    caller_agent.train(
        caller_training,
        epochs=400,
        batch_size=500,
        augmentation_factor=1,
        validation_split=0.2
    )
    caller_agent.persist(caller_model_path)

    callee_agent.train(
        callee_training,
        epochs=400,
        batch_size=500,
        augmentation_factor=1,
        validation_split=0.2
    )
    callee_agent.persist(callee_model_path)


class RasaDialogueManager(AbstractDialogueManager):

    def __init__(self, model_dir):
        self.agent = Agent.load(model_dir)
        self.acts = []

    def process_act(self, act, concepts):
        concept_string = json.dumps(concepts)
        rasa_msg = "/%s%s" % (act, concept_string)
        results = self.agent.handle_message(rasa_msg)
        self.acts.extend(results)

    def next_act(self):
        if not self.acts:
            return None, None
        act, entities = action_to_act(self.acts.pop(0))
        return act, entities

if __name__ == '__main__':
    train()