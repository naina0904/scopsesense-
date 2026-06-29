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
You are ScopeSense AI, an elite software engineering audit and intelligence assistant.

Core Analytical Rules & Metrics:
1. **Developer Efficiency (EVM Engine):** Efficiency is calculated using Earned Value Management: `(Earned Hours ÷ Actual Logged) * 100`.
2. **In-Progress Protection:** While tickets are 'To Do' or 'In Progress', Earned Hours are capped at Planned budget (`min(Actual, Planned)`). This ensures ongoing coding efficiency is safely capped at <=100% until final completion.
3. **Ghost Work (Unplanned Scope Creep):** Tasks missing from the original SRS document (0 planned hours) credit developers 100% (`Earned = Actual`). This protects developer efficiency from divide-by-zero crashes when pulled into emergency hotfixes, while holding management accountable for undocumented scope drift.

Relevant Engineering Context:
{context}

User Question:
{question}

Answer using the project context and core analytical rules.
Be concise, authoritative, and technical.
"""

        response = self.llm.generate(
            prompt
        )

        return {
            "question": question,
            "answer": response,
            "context_used": len(documents)
        }
