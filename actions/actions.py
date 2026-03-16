import os
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
from typing import Any, Text, Dict, List


# getting api key
API_KEY = os.getenv("FOOTBALL_API_KEY")
HEADERS = {
    "X-Auth-Token": API_KEY
}

class ActionGetInfo(Action):

    def name(self):
        return "action_getInfo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # entity extraction
        team = next(tracker.get_latest_entity_values("team"), None)
        last_opponent = next(tracker.get_latest_entity_values("lastOpponent"), None)
        last_score = next(tracker.get_latest_entity_values("lastScore"), None)
        league_pos = next(tracker.get_latest_entity_values("leaguePosition"), None)
        manager = next(tracker.get_latest_entity_values("manager"), None)
        next_game_date = next(tracker.get_latest_entity_values("nextGameDate"), None)
        next_opp = next(tracker.get_latest_entity_values("nextOpponent"), None)
        games_played = next(tracker.get_latest_entity_values("numGamesPlayed"), None)
        playing_now = next(tracker.get_latest_entity_values("playingNow"), None)
        win_loss = next(tracker.get_latest_entity_values("winLossRecord"), None)


        # handling edge cases
        if tracker.latest_message.get("intent", {}).get("name") == "backtrack":
            dispatcher.utter_message(response="utter_backtrack")
            return []
        
        if not team:
            dispatcher.utter_message(response="utter_missing_team")
            return []
        
        if team and not any([last_opponent, last_score, league_pos, manager, next_game_date, next_opp, games_played, playing_now, win_loss]):
            dispatcher.utter_message(response="utter_vague_question")
            return []


        # calling api
        api_url = "https://api.football-data.org/v4"
        try:
            PL_teams_url = f"{api_url}/competitions/2072/teams"
            response = requests.get(PL_teams_url)
            response.raise_for_status()
            teams_data = response.json()
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I was unable to fetch the Premier League data | Error -> {e}")
            return []
        

        # check if team in detected entity is even real
        if team not in teams_data:
            dispatcher.utter_message(response="utter_team_not_found")
            return []
        

        dispatcher.utter_message(text=f"found {team} on api")
        return []