from app.core.database import get_db


class CatalogRepository:
    def __init__(self):
        self._db = get_db()

    def get_categories(self) -> dict[str, str]:
        return {
            str(category["_id"]): category.get("name", "")
            for category in self._db.categories.find({}, {"name": 1})
        }

    def get_products(self) -> list[dict]:
        return list(
            self._db.products.find(
                {},
                {"name": 1, "description": 1, "price": 1, "category_ids": 1},
            )
        )