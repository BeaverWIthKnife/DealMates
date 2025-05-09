from data import CATEGORIES
from models import LobbyUserModel, LobbyModel, ProductModel, CategoryModel
from typing import List, Any, Dict


class Category:
    @staticmethod
    def get(contains: str) -> List[CategoryModel]:
        keys = []
        for key in CATEGORIES:
            if contains in key:
                keys.append(key)
        if not keys:
            keys = list(CATEGORIES.keys())
        
        return [
            CategoryModel(
                title=cat,
                products=len(CATEGORIES[cat])
            ) for cat in keys
        ]

    @staticmethod
    def products(category: str | None = "", contains: str = "", only_titles: bool = False) -> List[ProductModel] | List[str]:
        results = []
        
        if category:
            products = CATEGORIES.get(category, [])
        else: 
            products = []
            for cat_products in CATEGORIES.values():
                products.extend(cat_products)
        
        for p in products:
            if contains in p["title"]:
                if only_titles:
                    results.append(p["title"])
                else:
                    results.append(p)
        
        if not results and category:
            if only_titles:
                results = [p["title"] for p in CATEGORIES.get(category, [])]
            else:
                results = CATEGORIES.get(category, [])
        elif not results:
            if only_titles: 
                results = [p["title"] for p in products]
            else:
                results = products
                
        if only_titles:
            return results
        return [
            ProductModel(**prod) for prod in results
        ]



class Lobby:
    db = {}

    @classmethod
    def create_lobby(self, product: ProductModel):
        new_lobby = LobbyModel(
            common_price=product.price,
            bulk=product.price,
            unit=product.unit,
            users=[]
        )

        Lobby.db.setdefault(product.title, new_lobby.model_dump())
        return new_lobby
    
    @classmethod
    def set_lobby(self, product: str, key: Any, new_value: Any):
        lobby = Lobby.db[product]
        lobby[key] = new_value

        return lobby

    @classmethod
    def get_lobby(self, product: str, user_id: int | None = None):
        lobby = LobbyModel(**Lobby.db[product])
        users = lobby.users

        if user_id:
            for user in users:
                model = LobbyUserModel(**user)
                if model.id == user_id:
                    lobby.users = [model]
                    break
        
        return lobby
    
    
    @classmethod
    def set_user(self, id: int, product: str, key: Any, new_value: Any):
        users: List[Dict] = Lobby.db[product]["users"]

        for user in users:
            model = LobbyUserModel(**user)
            if model.id != id:
                continue
            user[key] = new_value
            return model
        
    @classmethod
    def add_user(cls, id: int, product: str, chat_id: int, menu_id: int | None = None):
        lobby_data = cls.db.get(product)
        if not lobby_data:
            raise ValueError(f"Лобі з продуктом '{product}' не знайдено.")

        lobby = LobbyModel(**lobby_data)

        # Проверка: уже есть такой юзер?
        for user in lobby.users:
            if user.id == id:
                return  # Уже в лобби

        new_user = LobbyUserModel(
            id=id,
            chat_id=chat_id,
            menu_id=menu_id or -1,
            wants=0,
            status=""
        )

        lobby.users.append(new_user.model_dump())
        cls.db[product] = lobby.model_dump()
    

    @classmethod
    def remove_user(cls, id: int, product: str):
        lobby_data = cls.db.get(product)
        if not lobby_data:
            raise ValueError(f"Лобі з продуктом '{product}' не знайдено.")

        lobby = LobbyModel(**lobby_data)

        # Фильтруем пользователей, исключая того, кого нужно удалить
        lobby.users = [
            user for user in lobby.users
            if user.id != id
        ]

        cls.db[product] = lobby.model_dump()
    
    @classmethod
    def get_bulk(cls, category: str, product_title: str, lobby: LobbyModel) -> float:
        # Получаем продукт из категории
        product = next((
            p for p in Category.products(category, product_title)
            if p.title == product_title
        ), None)

        if not product:
            raise ValueError(f"Продукт '{product_title}' не знайдено в категорії '{category}'.")

        # Считаем общее количество заказов
        total_wants = sum(user.wants for user in lobby.users)

        # Сортируем bulk'и от большего к меньшему (по минимальному количеству)
        bulks_sorted = sorted(product.bulks, key=lambda b: b.range[0], reverse=True)

        for bulk_option in bulks_sorted:
            if bulk_option.range[0] <= total_wants <= bulk_option.range[1]:
                return bulk_option.unit_price

        # Если количество больше самого большого диапазона — возвращаем минимальную цену
        if total_wants > bulks_sorted[0].range[1]:
            return bulks_sorted[0].unit_price

        # Если не подошло ни под один диапазон — возвращаем обычную цену
        return product.price





def merge_product_info(product: ProductModel):
    lobby = Lobby.get_lobby(product.title)
    
    title = f"{product.title} 👥{len(lobby.users)}"

    description = (
        f"Ціна без опту {product.price}грн\n"
        f"Ціна зараз {lobby.bulk}грн"
    )

    return {
        "title": title,
        "description": description
    }






if __name__ == "__main__":
    for prod in Category.products("", "", False):
        Lobby.create_lobby(prod)
    
    r = Category.products("", "л", True)[0]
    Lobby.add_user(
        id=834778435745,
        chat_id=1,
        menu_id=12,
        product="Чіпси"
    )

    # Lobby.remove_user(
    #     834778435745,
    #     "Чіпси"
    # )

    Lobby.set_user(
        834778435745,
        "Чіпси",
        "status",
        "✅"
    )

    Lobby.set_lobby("Чіпси", "bulk", 999999999999999.0)

    l = Lobby.get_lobby("Чіпси")
    print(l)

    print(Lobby.db)