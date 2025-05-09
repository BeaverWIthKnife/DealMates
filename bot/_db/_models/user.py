from beanie import Document, Indexed
from pydantic import BaseModel


class UserModel(Document):
    id: Indexed(int)
    lobby_id: Indexed(str)


class LobbyUserModel(BaseModel):
    id: int
    wants: int
    payed: bool
    status: str