from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionGetInfo(Action):

    def name(self):
        return "action_getInfo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):
        team = tracker.get_slot("team")

        if not team:
            dispatcher.utter_message(response="utter_missing_team")
            return []
        
        dispatcher.utter_message(text=f"placeholder info for {team}")
        return []