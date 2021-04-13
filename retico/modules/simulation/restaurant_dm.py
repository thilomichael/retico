from retico.core import abstract
from retico.core.text.common import GeneratedTextIU
from retico.core.dialogue.common import DialogueActIU
from retico.core.prosody.common import EndOfTurnIU


class RestaurantDialogueManager(abstract.AbstractModule):
    @staticmethod
    def name():
        return "Restaurant DM Module"

    @staticmethod
    def description():
        return "A dialogue manager that can find restaurants"

    @staticmethod
    def input_ius():
        return [DialogueActIU, EndOfTurnIU]

    @staticmethod
    def output_iu():
        return GeneratedTextIU

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.food_type = None
        self.area = None
        self.price = None
        self.current_da = None

    def generateQuestion(self):
        if self.food_type is None:
            return "What type of food would you like to eat?"
        if self.area is None:
            return "Where would you like to eat?"
        if self.price is None:
            return "In what price range do you want to eat?"
        return None

    def generateText(self, da):
        if da.act == "greet":
            return "Hello! I can help you find a restaurant."
        if da.act == "inform":
            if da.concepts.get("cuisine"):
                self.food_type = da.concepts["cuisine"]
            if da.concepts.get("price"):
                if da.concepts["price"] == "lo":
                    self.price = "cheap"
                else:
                    self.price = "expensive"
            if da.concepts.get("location"):
                self.area = da.concepts["location"]
            q = self.generateQuestion()
            if q is not None:
                return "Okay. " + q
            return f"Okay. You want to eat {self.price} {self.food_type} food in the {self.area} of the town, correct?"

        elif da.act == "affirm":
            q = self.generateQuestion()
            if q is not None:
                return "Okay. " + q
            return "I have the following restaurant for you: The generic restaurant at main street 123."
        else:
            return "Sorry, I could not understand you."

    def process_iu(self, input_iu):
        if isinstance(input_iu, DialogueActIU):
            self.current_da = input_iu
        elif isinstance(input_iu, EndOfTurnIU):
            out = self.create_iu(input_iu)
            out.dispatch = True
            out.payload = self.generateText(self.current_da)
            return out

    def shutdown(self):
        self.area = None
        self.price = None
        self.current_da = None
        self.food_type = None
