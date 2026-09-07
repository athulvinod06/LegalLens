"""
Grounded Conversational Question-Answering Service (RAG) for LegalLens (Phase 5).
Retrieves relevant clauses from the vector store and synthesizes grounded answers
with explicit clause citations. Refuses to hallucinate beyond provided clauses.
"""

import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.ml.vector_store import vector_store_service, ContractVectorStore


class QAResponse(BaseModel):
    question: str
    answer: str
    citations: List[int]
    retrieved_clauses: List[Dict[str, Any]]
    is_grounded: bool
    disclaimer: str = (
        "LegalLens is an automated first-pass contract analysis tool. "
        "Every answer is grounded strictly in source clauses. "
        "Not legal advice."
    )


class GroundedQAEngine:
    """
    Grounded QA Engine enforcing constitutional RAG rules:
    1. Direct citations to source clauses ([Clause X])
    2. Explicit refusal if the contract does not address the question
    3. User account isolation
    """

    def __init__(self, vector_store: Optional[ContractVectorStore] = None):
        self.vector_store = vector_store or vector_store_service
        self.llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    def answer_question(
        self,
        user_id: str,
        contract_id: str,
        question: str,
        top_k: int = 3
    ) -> QAResponse:
        """
        Executes semantic retrieval and grounded answer generation.
        """
        # 1. Semantic Retrieval
        retrieved = self.vector_store.search(user_id, contract_id, question, top_k=top_k)

        # 2. Constitutional Out-of-Scope / Refusal Check
        # If no clauses retrieved or max similarity is negligible (< 0.18)
        if not retrieved or retrieved[0]["similarity"] < 0.18:
            return QAResponse(
                question=question,
                answer="The contract does not address this question based on the retrieved clauses.",
                citations=[],
                retrieved_clauses=[],
                is_grounded=False,
            )

        top_clause = retrieved[0]
        # Check if the highest similarity clause is actually relevant
        q_lower = question.lower()
        has_context_overlap = any(
            word in top_clause["text"].lower() or word in top_clause["category"].lower()
            for word in q_lower.split() if len(word) > 3
        )

        if not has_context_overlap and top_clause["similarity"] < 0.35:
            return QAResponse(
                question=question,
                answer="The contract does not address this question based on the retrieved clauses.",
                citations=[],
                retrieved_clauses=retrieved,
                is_grounded=False,
            )

        # 3. Grounded Answer Synthesis
        citations = [c["clause_id"] for c in retrieved if c["similarity"] >= 0.20]

        # Call real LLM API if configured, else use grounded template synthesizer
        if self.llm_provider == "openai" and self.openai_api_key and self.openai_api_key != "mock_key":
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_api_key)
                context_str = "\n\n".join(
                    f"[Clause {c['clause_id']}: {c['title']}]\n{c['text']}" for c in retrieved
                )
                prompt = (
                    f"You are LegalLens. Answer the user question based ONLY on the provided contract clauses.\n"
                    f"Cite each supporting claim using [Clause X].\n"
                    f"If the clauses do not contain the answer, say exactly: "
                    f"'The contract does not address this question based on the retrieved clauses.'\n\n"
                    f"Retrieved Clauses:\n{context_str}\n\n"
                    f"Question: {question}"
                )
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                answer_text = resp.choices[0].message.content.strip()
            except Exception:
                answer_text = self._synthesize_grounded_answer(question, retrieved)
        else:
            answer_text = self._synthesize_grounded_answer(question, retrieved)

        return QAResponse(
            question=question,
            answer=answer_text,
            citations=citations,
            retrieved_clauses=retrieved,
            is_grounded=True,
        )

    def _synthesize_grounded_answer(self, question: str, retrieved_clauses: List[Dict[str, Any]]) -> str:
        """
        Deterministic, rule-grounded answer synthesizer for local development and unit tests.
        Strictly cites clauses and quotes factual details.
        """
        top = retrieved_clauses[0]
        cid = top["clause_id"]
        cnum = top["clause_number"]
        title = top["title"]
        text = top["text"]

        # Summarize relevant rule based on question keywords
        q_lower = question.lower()
        if "terminate" in q_lower or "notice" in q_lower or "cancel" in q_lower:
            return f"According to [{cnum}: {title}], {text}"
        elif "pay" in q_lower or "fee" in q_lower or "rate" in q_lower or "salary" in q_lower:
            return f"Under [{cnum}: {title}], the payment provisions state: {text}"
        elif "confidential" in q_lower or "secret" in q_lower or "nda" in q_lower:
            return f"Pursuant to [{cnum}: {title}], the confidentiality terms specify that: {text}"
        elif "liab" in q_lower or "damages" in q_lower or "cap" in q_lower:
            return f"As defined in [{cnum}: {title}], liability is governed as follows: {text}"
        else:
            return f"Based on [{cnum}: {title}], the contract provides: {text}"


# Default singleton instance
qa_engine_service = GroundedQAEngine()
