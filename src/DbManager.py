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

    def createUser(self, username: str, ip: str) -> None:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        db["user"][ip] = {}
        db["user"][ip]["team"] = 0
        db["user"][ip]["name"] = username
        db["teams"]["0"]["user_count"] += 1

        with open(self._db_path, "w") as js:
            json.dump(db, js, indent=4)

    def getUser(self, ip: str) -> dict:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        return db["user"][ip]

    def getUsers(self) -> dict:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        return db["user"]

    def assignTeam(self, user: str, team: int) -> None:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        oldTeam: str = str(db["user"][user]["team"])
        db["teams"][oldTeam]["user_count"] -= 1
        if db["teams"][oldTeam]["user_count"] <= 0:
            del db["teams"][oldTeam]
        db["user"][user]["team"] = team
        db["teams"][str(team)]["user_count"] += 1

        with open(self._db_path, "w") as js:
            json.dump(db, js, indent=4)

    def getTeams(self) -> list:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        teams: list = list(db["teams"].values())
        for team in teams:
            team["research_field"] = db["research_field"][team["research_field"]]
        return teams

    def createTeam(self, name: str, color: str,
                   research_field: str, creator: str) -> int:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
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

        id: int = largest+1
        db["teams"][str(id)] = team

        with open(self._db_path, "w") as js:
            json.dump(db, js, indent=4)

        return id

    def hasGameStarted(self) -> bool:
        db: dict = dict()
        with open(self._db_path, "r") as js:
            db: dict = json.load(js)
        return db["game"]["state"]["started"]
