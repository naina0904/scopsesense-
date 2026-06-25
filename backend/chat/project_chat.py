from backend.llm.manager import (
    LLMManager
)

from backend.semantic.vector_store import (
    VectorStore
)


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

        prompt = f"""
You are ScopeSense AI.

You are analyzing a software engineering project.

Relevant Engineering Context:
{context}

User Question:
{question}

Answer using the project context.
Be concise and technical.
"""

        response = self.llm.generate(
            prompt
        )

        return {
            "question": question,
            "answer": response,
            "context_used": len(documents)
        }
