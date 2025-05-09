from beanie import Document, Indexed
from typing import List, Dict


class LobbyModel(Document):
    lobby_id: Indexed(str)
    people: List[Dict]
