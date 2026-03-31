from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


class OpenRouterClient:
    def is_enabled(self) -> bool:
        return bool(settings.openrouter_api_key)

    def generate_answer(self, question: str, context: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Answer only with facts grounded in the retrieved catalog context. If the answer is not present, say so explicitly.",
                ),
                (
                    "human",
                    "Question:\n{question}\n\nCatalog context:\n{context}",
                ),
            ]
        )
        chain = prompt | self._build_llm() | StrOutputParser()
        return chain.invoke({"question": question, "context": context})

    @staticmethod
    def _build_llm() -> ChatOpenAI:
        return ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=0.2,
            timeout=30,
            max_retries=2,
            default_headers={
                "HTTP-Referer": settings.openrouter_referer,
                "X-Title": settings.openrouter_app_name,
            },
        )