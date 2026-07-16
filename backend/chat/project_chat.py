from backend.llm.manager import (
    LLMManager
)

from backend.semantic.vector_store import (
    VectorStore
)
from backend.chat.user_guide_context import get_user_guide_context


class ProjectChat:

    def __init__(
        self,
        provider="groq"
    ):

        self.llm = LLMManager(
            provider=provider
        )

        self.vector_store = VectorStore()

    def ask(
        self,
        question
    ):

        try:

            relevant_context = (
                self.vector_store.search_similar_commits(
                    question,
                    limit=10
                )
            )

        except Exception:

            relevant_context = {

                "documents":
                    [[]]
            }

        documents = (
            relevant_context.get(
                "documents",
                [[]]
            )[0]
        )

        context = "\n".join(documents)

        user_guide_knowledge = get_user_guide_context()
        prompt = f"""
You are ScopeSense AI, an elite software engineering audit and intelligence assistant.

{user_guide_knowledge}

Relevant Engineering Context from Vector Store:
{context}

User Question:
{question}

Answer using the canonical user guide logic, formulas, and project context above.
Be concise, authoritative, and helpful.
"""

        response = self.llm.generate(
            prompt
        )

        return {
            "question": question,
            "answer": response,
            "context_used": len(documents)
        }
