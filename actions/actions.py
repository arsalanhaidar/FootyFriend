from datetime import datetime
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
if not API_KEY:
    raise ValueError("api key not set in environment variable")


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

        intent = tracker.latest_message.get("intent", {}).get("name")


        # handling repairs
        if intent == "backtrack":
            dispatcher.utter_message(response="utter_backtrack")
            return []
        
        if not team:
            dispatcher.utter_message(response="utter_missing_team")
            return []
        
        if not any([last_opponent, last_score, league_pos, manager, next_game_date, next_opp, games_played, playing_now, win_loss]):
            dispatcher.utter_message(response="utter_vague_question")
            return []


        # calling api
        try:
            PL_teams_url = "https://api.football-data.org/v4/competitions/PL/teams"
            response = requests.get(PL_teams_url, headers=HEADERS)
            PL_teams_data = response.json()
            PL_teams = PL_teams_data.get("teams", [])
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I was unable to fetch the Premier League data | Error -> {e}")
            return []
        

        # check if team in detected entity is even real
        team_data = None

        for t in PL_teams:
            if team.lower() in t["name"].lower():
                team_data = t
                break
        if not team_data:
            dispatcher.utter_message(response="utter_team_not_found")
            return []
        
        team_name = team_data["name"]
        team_id = team_data["id"]


#################################################################
# this section handles everything to do with the detected slots #
#################################################################


        matches_url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=10"
        matches_response = requests.get(matches_url, headers=HEADERS)
        matches = matches_response.json()["matches"]
        finished_matches = [m for m in matches if m["status"] == "FINISHED"]
        upcoming_matches = [m for m in matches if m["status"] == "SCHEDULED"]


        if last_opponent or last_score:
            if finished_matches:
                match = finished_matches[-1]

                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]

                home_goals = match["score"]["fullTime"]["home"]
                away_goals = match["score"]["fullTime"]["away"]

                opponent = away if home == team_name else home

                if last_opponent:
                    dispatcher.utter_message(
                        text=f"{team_name}'s last game was against {opponent} "
                    )

                if last_score:
                    if opponent == away:
                        dispatcher.utter_message(
                            text=f"The score in {team_name}'s last game was -> {team_name}: {home_goals} | {opponent}: {away_goals}"
                        )
                    elif opponent == home:
                        dispatcher.utter_message(
                            text=f"The score in {team_name}'s last game was -> {team_name}: {away_goals} | {opponent}: {home_goals}"
                        )

        
        if next_opp:
            if upcoming_matches:
                match = upcoming_matches[0]

                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]

                opponent = away if home == team_name else home

                dispatcher.utter_message(
                    text=f"{team_name}'s next game is against {opponent}"
                )
            
        
        if games_played:
            games_played_url = "https://api.football-data.org/v4/competitions/PL/standings"
            games_played_response = requests.get(games_played_url, headers=HEADERS)
            standings = games_played_response.json()
            table = standings["standings"][0]["table"]

            for team_row in table:
                if team_row["team"]["id"] == team_id:
                    played = team_row["playedGames"]

                    dispatcher.utter_message(
                        text=f"{team_name} have played {played} games so far this season"
                    )
                

        if next_game_date:
            next_date_url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=SCHEDULED"
            next_date_response = requests.get(next_date_url, headers=HEADERS)
            next_matches = next_date_response.json()["matches"]

            if next_matches:
                next_match = next_matches[0]

                date = datetime.fromisoformat(next_match["utcDate"].replace("Z", ""))
                pretty_date = date.strftime("%d %B at %H:%M")
                home = next_match["homeTeam"]["name"]
                away = next_match["awayTeam"]["name"]

                dispatcher.utter_message(
                    text=f"{team_name}'s next game is {home} vs {away} on {pretty_date}"
                )
        

        if manager:
            coach = team_data.get("coach", {}).get("name")

            if coach:
                dispatcher.utter_message(
                    text=f"{team_name}'s manager is {coach}"
                )
            else:
                dispatcher.utter_message(
                    text=f"I couldn't find the manager for {team_name}"
                )
        

        if league_pos:
            league_pos_url = "https://api.football-data.org/v4/competitions/PL/standings"
            league_pos_response = requests.get(league_pos_url, headers=HEADERS)
            league_positions = league_pos_response.json()
            league_table = league_positions["standings"][0]["table"]

            for team_row in league_table:
                if team_row["team"]["id"] == team_id:
                    position = team_row["position"]

                    dispatcher.utter_message(
                        text=f"{team_name} are currently {position} in the Premier League"
                    )
            

        if playing_now:
            playing_now_url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=LIVE"
            playing_now_response = requests.get(playing_now_url, headers=HEADERS)
            live_matches = playing_now_response.json()["matches"]

            if live_matches:
                dispatcher.utter_message(
                    text=f"{team_name} are currently playing right now"
                )
            else:
                dispatcher.utter_message(
                    text=f"{team_name} are not playing right now"
                )


        if win_loss:
            win_loss_url = "https://api.football-data.org/v4/competitions/PL/standings"
            win_loss_response = requests.get(win_loss_url, headers=HEADERS)
            win_loss_table = win_loss_response.json()["standings"][0]["table"]

            for team_row in win_loss_table:
                if team_row["team"]["id"] == team_id:
                    wins = team_row["won"]
                    draws = team_row["draw"]
                    loss = team_row["lost"]

                    dispatcher.utter_message(
                        text=f"{team_name}'s win-loss record is: {wins} wins | {draws} draws | {loss} losses"
                    )


        return []