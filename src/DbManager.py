import json
import math
import random

from PathManager import PathsManager


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')

    if len(hex_color) != 6:
        raise ValueError("Ungültiger Hex-Farbwert. Erwarte Format #RRGGBB")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return r, g, b


class DB:
    def __init__(self, path: str):
        self._db_path: str = path

    def _load_db(self) -> dict:
        db: dict = dict()
        with open(self._db_path, "r", encoding="utf-8") as js:
            db: dict = json.load(js)
        return db

    def _write_db(self, new: dict) -> None:
        def update_nested(original: dict, pushed: dict) -> None:
            for key, value in pushed.items():
                if isinstance(value, dict) and key in original:
                    # Wenn es ein verschachteltes Objekt ist, rekursiv aktualisieren
                    update_nested(original[key], value)
                else:
                    # Direkt aktualisieren
                    original[key] = value
        db: dict = self._load_db()
        update_nested(db, new)
        with open(self._db_path, "w", encoding="utf-8") as js:
            json.dump(db, js, indent=4)

    def create_user(self, username: str, ip: str) -> None:
        db: dict = self._load_db()
        db["user"][ip] = {}
        db["user"][ip]["team"] = -1
        db["user"][ip]["name"] = username
        db["user"][ip]["is_at_game"] = False
        self._write_db(db)

    def get_user(self, ip: str) -> dict:
        db: dict = self._load_db()
        return db["user"][ip]

    def get_users(self) -> dict:
        db: dict = self._load_db()
        return db["user"]

    def is_user(self, ip: str) -> bool:
        db: dict = self._load_db()
        try:
            _ = db["user"][ip]
            return True
        except KeyError:
            return False

    def get_chosen_country(self, ip: str) -> str:
        db: dict = self._load_db()
        return db["teams"][str(self.get_team(ip))]["chosen_country"][ip]

    def get_team(self, ip: str) -> int:
        db: dict = self._load_db()
        return int(db["user"][ip]["team"])

    def assign_team(self, user: str, team: int) -> None:
        db: dict = self._load_db()
        oldTeam: str = str(db["user"][user]["team"])
        if int(oldTeam) >= 0:
            if oldTeam == str(team):
                return
            db["teams"][oldTeam]["user_count"] -= 1
            del db["teams"][oldTeam]["chosen_country"][user]
            if db["teams"][oldTeam]["user_count"] <= 0:
                r_id: str = str(db["teams"][oldTeam]["research_field"])
                del db["teams"][oldTeam]
                del db["game"]["progress"][r_id][oldTeam]
        db["user"][user]["team"] = team
        db["teams"][str(team)]["user_count"] += 1
        db["teams"][str(team)]["chosen_country"][user] = ""

        self._write_db(db)

    def get_teams(self) -> list:
        db: dict = self._load_db()
        teams: list = list(db["teams"].values())
        for team in teams:
            team["research_field"] = db["research_field"][team["research_field"]]
        return teams

    def is_team(self, name: str) -> bool:
        db: dict = self._load_db()
        for k, team in db["teams"].items():
            if team["name"] == name: return True
        return False

    def get_team_by_name(self, name: str) -> int:
        db: dict = self._load_db()
        for k, team in db["teams"].items():
            if team["name"] == name: return int(k)
        return -1

    def create_team(self, name: str, color: str,
                    research_field: str, creator: str) -> int:
        db: dict = self._load_db()
        fields: list = db["research_field"]
        for i in range(len(fields)):
            if fields[i] == research_field:
                break
        creator: str = db["user"][creator]["name"]
        team: dict = {
            "name": name,
            "color": hex_to_rgb(color),
            "research_field": i,
            "creator": creator,
            "country": "",
            "user_count": 0,
            "chosen_country": {},
            "investoren": [],
            "current_investors": [0, 1, 2, 3, 4],
            "current_milestone": 0,
            "paid_milestone": 0,
            "destruction_degree": 0,
            "done": False,
            "killed": 0
        }
        largest: int = -1
        for key in db["teams"].keys():
            largest = max(int(key), largest)
        t_id: int = largest + 1
        db["teams"][str(t_id)] = team
        db["game"]["progress"][str(i)][t_id] = 0
        self._write_db(db)
        return t_id

    def set_team_country(self, team: int) -> None:
        db = self._load_db()
        chosen_country: dict = db["teams"][str(team)]["chosen_country"]
        countries: dict = dict()
        for k, v in chosen_country.items():
            if v in countries.keys():
                countries[v] += 1
            else:
                countries[v] = 1
        largest: int = -1
        for k, v in countries.items():
            largest: int = max(v, largest)
        last_ones: list = []
        for k, v in countries.items():
            if v == largest:
                last_ones.append(k)
        if len(last_ones) > 1:
            for k, v in db["countries"].items():
                if k in last_ones:
                    last_ones: list = [k]
                    break
        chosen_one: str = last_ones[0]
        db["teams"][str(team)]["country"] = chosen_one
        self._write_db(db)

    def is_in_team(self, ip: str) -> bool:
        return self.get_team(ip) >= 0

    def get_team_name(self, team: int) -> str:
        db = self._load_db()
        return db["teams"][str(team)]["name"]

    def get_team_country(self, team: int) -> str:
        db = self._load_db()
        return db["teams"][str(team)]["country"]

    def have_all_chosen_country(self, team: int) -> bool:
        db: dict = self._load_db()
        selectedCountries: dict = db["teams"][str(team)]["chosen_country"]
        for k, v in selectedCountries.items():
            if v == "":
                return False
        return True

    def get_team_votes(self) -> dict:
        db: dict = self._load_db()
        countries: dict = {k: {} for k, _ in db["countries"].items()}
        teams: list = self.get_teams()
        for country, dic in countries.items():
            for team in teams:
                for user, cou in team["chosen_country"].items():
                    if country == cou:
                        if team["name"] in dic.keys():
                            dic[team["name"]] += 1
                        else:
                            dic[team["name"]] = 1
        return countries

    def get_user_flag(self, ip: str) -> str:
        db: dict = self._load_db()
        path_manager: PathsManager = PathsManager()
        team: int = self.get_team(ip)
        country: str = db["teams"][str(team)]["country"]
        return path_manager.get_path("country_flag_url", country)

    def get_user_color(self, ip: str) -> list:
        db: dict = self._load_db()
        return db["teams"][str(self.get_team(ip))]["color"]

    def get_user_technology(self, ip: str) -> str:
        db: dict = self._load_db()
        return db["research_field"][db["teams"][str(self.get_team(ip))]["research_field"]]

    def get_user_technology_description(self, ip: str) -> str:
        db: dict = self._load_db()
        return db["research_field_description"][db["teams"][str(self.get_team(ip))]["research_field"]]

    def get_user_investor_history(self, ip: str) -> dict:
        db: dict = self._load_db()
        team: str = str(self.get_team(ip))
        return db["teams"][team]["investoren"]

    def get_user_milestone(self, ip: str) -> dict:
        db: dict = self._load_db()
        team: str = str(self.get_team(ip))
        research_field: str = db["research_field"][db["teams"][team]["research_field"]]
        milestone: int = db["teams"][team]["current_milestone"]
        return db["milestones"][research_field][milestone]

    def get_user_investoren(self, ip: str) -> list:
        db: dict = self._load_db()
        team: str = str(self.get_team(ip))
        investoren: list = db["teams"][team]["current_investors"]
        sending_investoren: list = list()
        for i in investoren:
            i = str(i)
            sending_investoren.append(db["game"]["investoren"][i])
        return sending_investoren

    def bought_investor(self, index: int, ip: str) -> None:
        db: dict = self._load_db()
        team: str = str(self.get_team(ip))
        investor: str = str(db["teams"][team]["current_investors"][index])
        name: str = db["game"]["investoren"][investor]["name"]
        price: int = db["game"]["investoren"][investor]["price"]
        country_index: float = db["countries"][db["teams"][team]["country"]]
        destruction_degree: int = db["game"]["investoren"][investor]["destruction_degree"]
        if len(db["teams"][team]["investoren"]) == 0:
            db["teams"][team]["investoren"].append([name, price])
        else:
            db["teams"][team]["investoren"].insert(0, [name, price])
        db["teams"][team]["paid_milestone"] += (price * country_index)
        milestone_needed: int = db["game"]["technology_price_constant"] // 10
        db["teams"][team]["destruction_degree"] += destruction_degree
        while True:
            new_inves: int = random.randint(0, 16)
            if new_inves not in db["teams"][team]["current_investors"]:
                db["teams"][team]["current_investors"][index] = new_inves
                break

        self._write_db(db)
        if db["teams"][team]["paid_milestone"] >= milestone_needed:
            self.next_milestone(team)
        self.update_progress(team)

    def next_milestone(self, team: str) -> None:
        db: dict = self._load_db()
        db["teams"][team]["current_milestone"] += 1
        db["teams"][team]["paid_milestone"] = 0
        if db["teams"][team]["current_milestone"] > 9:
            db["teams"][team]["destruction_degree"] = db["teams"][team]["destruction_degree"] / len(db["teams"][team]["investoren"])
            db["teams"][team]["done"] = True
        self._write_db(db)

    def set_country(self, ip: str, country: str) -> None:
        db: dict = self._load_db()
        db["teams"][str(self.get_team(ip))]["chosen_country"][ip] = country
        self._write_db(db)

    def has_game_started(self) -> bool:
        db: dict = self._load_db()
        return db["game"]["state"]["started"]

    def update_progress(self, team: str) -> None:
        db: dict = self._load_db()
        amount_milestone: int = db["teams"][team]["current_milestone"]
        paid_milestone: int = db["teams"][team]["paid_milestone"]
        tp_constant: int = db["game"]["technology_price_constant"]
        progress: float = ((amount_milestone * (tp_constant // 10) + paid_milestone) / tp_constant) * 100.0
        progress = math.floor(progress * 100) / 100
        research: str = str(db["teams"][team]["research_field"])
        db["game"]["progress"][research][team] = progress
        self._write_db(db)

    def get_progress(self, team: int) -> float:
        db: dict = self._load_db()
        try:
            research: str = str(db["teams"][team]["research_field"])
            return db["game"]["progress"][research][str(team)]
        except KeyError:
            return 0

    def get_milestone_progress(self, team: int) -> float:
        db: dict = self._load_db()
        paid_milestone: int = db["teams"][str(team)]["paid_milestone"]
        tp_constant: int = db["game"]["technology_price_constant"]
        milestone_progress: float = (paid_milestone / (tp_constant / 10)) * 100
        milestone_progress = math.floor(milestone_progress * 100) / 100
        return milestone_progress

    def is_team_done(self, team: int) -> bool:
        db: dict = self._load_db()
        return db["teams"][str(team)]["done"]

    def user_at_game(self, ip: str) -> None:
        db: dict = self._load_db()
        db["user"][ip]["is_at_game"] = True
        self._write_db(db)

    def get_leaderboards(self) -> dict:
        db: dict = self._load_db()
        leaderboards: dict = dict()
        for name in db["research_field"]:
            leaderboards[name] = []

        if len(db["teams"]) == 0:
            return leaderboards

        for r_id, k in enumerate(leaderboards.keys()):
            teams: dict = db["game"]["progress"][str(r_id)]
            teams: list = sorted(teams.items(), key=lambda x: x[1])
            for team in teams:
                team_id: str = str(team[0])
                db_team: dict = db["teams"][team_id]
                team_dict: dict = dict()
                team_dict["name"] = db_team["name"]
                team_dict["color"] = db_team["color"]
                flagUrl: str = PathsManager().get_path(*db["country_to_flag"][db_team["country"]])
                team_dict["country"] = flagUrl
                team_dict["progress"] = team[1]
                team_dict["members"] = []
                for user in db["user"].values():
                    if user["team"] != int(team_id):
                        continue
                    team_dict["members"].append(user["name"])
                leaderboards[k].append(team_dict)

        return leaderboards

    def get_top_three(self, ip: str) -> list:
        leaderboards: dict = self.get_leaderboards()
        team: str = str(self.get_team(ip))
        top_three: list = list()
        db: dict = self._load_db()
        r_ind: int = db["teams"][team]["research_field"]
        field: str = db["research_field"][r_ind]
        leaderboard: list = leaderboards[field]
        if len(leaderboard) >= 3:
            leaderboard: list = leaderboard[:3]
        for team in leaderboard:
            name: str = team["name"]
            progress: str = str(team["progress"])
            progress.replace(".",",")
            top_three.append(f"{name} | {progress}%")
        return top_three

    def get_killed(self, ip: str) -> str:
        db: dict = self._load_db()
        people: int = db["people"]
        destruction: float = db["teams"][str(self.get_team(ip))]["destruction_degree"]
        killed: int = math.floor(people * destruction)
        db["teams"][str(self.get_team(ip))]["killed"] = killed
        self._write_db(db)
        return f"{killed:,}".replace(",", " ")

    def start_game(self):
        db: dict = self._load_db()
        db["game"]["state"]["started"] = True
        self._write_db(db)

    def end_game(self):
        db: dict = self._load_db()
        db["game"]["state"]["started"] = False
        self._write_db(db)

    def get_db(self) -> dict:
        return self._load_db()

    def set_db(self, new: dict) -> None:
        self._write_db(new)

    def push_db(self, changes: dict) -> None:
        self._write_db(changes)

    def reset(self):
        db: dict = self._load_db()
        db["user"] = {}
        db["teams"] = {}
        db["game"]["id"] = 0
        db["game"]["teams"] = []
        db["game"]["progress"] = {"0": {}, "1": {}}
        db["game"]["state"]["started"] = False
        self._write_db(db)
