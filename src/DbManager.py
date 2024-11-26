import json

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