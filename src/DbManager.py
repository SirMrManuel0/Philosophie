import json


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')

    if len(hex_color) != 6:
        raise ValueError("Ungültiger Hex-Farbwert. Erwarte Format #RRGGBB")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


class DB:
    def __init__(self, path: str):
        self._db_path: str = path

    def _load_db(self) -> dict:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        return db

    def _write_db(self, new: dict) -> None:
        with open(self._db_path, "w") as js:
            json.dump(new, js, indent=4)

    def create_user(self, username: str, ip: str) -> None:
        db: dict = self._load_db()
        db["user"][ip] = {}
        db["user"][ip]["team"] = -1
        db["user"][ip]["name"] = username
        db["teams"]["0"]["user_count"] += 1
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
                del db["teams"][oldTeam]
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
            "chosen_country": {}
        }
        largest: int = -1
        for key in db["teams"].keys():
            largest = max(int(key), largest)
        id: int = largest + 1
        db["teams"][str(id)] = team
        self._write_db(db)
        return id

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


    def set_country(self, ip: str, country: str) -> None:
        db: dict = self._load_db()
        db["teams"][str(self.get_team(ip))]["chosen_country"][ip] = country
        self._write_db(db)

    def has_game_started(self) -> bool:
        db: dict = self._load_db()
        return db["game"]["state"]["started"]
