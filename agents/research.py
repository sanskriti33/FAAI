"""
Agent 3 — Research Agent
Performs TF-IDF document retrieval and cited evidence extraction.
"""

from typing import List, Dict, Any, Optional
from retrieval.document_retriever import DocumentRetriever
from orchestration.state import AuditState
from config import DEFAULT_TOP_K


class ResearchAgent:
    """
    Research Agent responsible for RAG evidence retrieval.
    Extracts relevant excerpts from vendor documents and scores similarity.
    """

    def __init__(self, retriever: Optional[DocumentRetriever] = None):
        self.retriever = retriever or DocumentRetriever()

    def execute_research(
        self,
        state: AuditState,
        query: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Executes document retrieval for the audit query and attaches results to state.
        """
        search_query = query or state.user_query
        state.log_event(
            agent_name="Research Agent",
            event_type="ACTION",
            message=f"ACTION 1: Querying document index for '{state.vendor_name}' using TF-IDF (top_k={top_k}).",
            payload={"query": search_query, "vendor": state.vendor_name}
        )

        retrieved_chunks = self.retriever.retrieve(
            vendor_name=state.vendor_name,
            query=search_query,
            top_k=top_k
        )

        state.research_results = retrieved_chunks

        # Format observation
        top_doc_info = [f"[{c['doc_id']}] (score: {c['score']:.2f})" for c in retrieved_chunks]
        summary_msg = f"Retrieved {len(retrieved_chunks)} evidence chunks: " + ", ".join(top_doc_info)

        state.log_event(
            agent_name="Research Agent",
            event_type="OBSERVATION",
            message=summary_msg,
            payload={"chunks": retrieved_chunks}
        )
        return retrieved_chunks

    def targeted_followup_search(
        self,
        state: AuditState,
        topic_query: str
    ) -> List[Dict[str, Any]]:
        """
        Executes a targeted secondary search (e.g., for remediation history or CAPA).
        """
        state.log_event(
            agent_name="Research Agent",
            event_type="ACTION",
            message=f"Executing targeted secondary search for: '{topic_query}'."
        )

        chunks = self.retriever.retrieve(
            vendor_name=state.vendor_name,
            query=topic_query,
            top_k=1
        )

        # Merge new chunks avoiding duplicates
        existing_ids = {c["doc_id"] for c in state.research_results}
        for c in chunks:
            if c["doc_id"] not in existing_ids:
                state.research_results.append(c)

        return chunks
