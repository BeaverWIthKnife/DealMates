from beanie import Document, Indexed


class ProductModel(Document):
    id: Indexed(int)
    lobby_id: Indexed(str)