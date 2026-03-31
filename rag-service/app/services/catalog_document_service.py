from langchain_core.documents import Document

from app.repositories.catalog_repository import CatalogRepository


class CatalogDocumentService:
    def __init__(self, catalog_repository: CatalogRepository):
        self._catalog_repository = catalog_repository

    def build_documents(self) -> list[Document]:
        categories = self._catalog_repository.get_categories()
        documents: list[Document] = []

        for product in self._catalog_repository.get_products():
            category_names = [
                categories.get(str(category_id), "")
                for category_id in product.get("category_ids", [])
            ]
            category_names = [name for name in category_names if name]

            documents.append(
                Document(
                    page_content=self._format_content(product, category_names),
                    metadata={
                        "product_id": str(product["_id"]),
                        "name": product.get("name", ""),
                        "description": product.get("description", ""),
                        "price": product.get("price"),
                        "categories": category_names,
                    },
                )
            )

        return documents

    @staticmethod
    def _format_content(product: dict, category_names: list[str]) -> str:
        return "\n".join(
            [
                f"Product: {product.get('name', '')}",
                f"Description: {product.get('description', '')}",
                f"Price: {product.get('price', '')}",
                f"Categories: {', '.join(category_names)}",
            ]
        )