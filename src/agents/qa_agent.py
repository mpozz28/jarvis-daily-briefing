import difflib
import json
import logging
import time
import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from src.llm_router import llm_router

logger = logging.getLogger(__name__)


class QAAgent:
    def __init__(self):
        pass

    def identify_relevant_item(
        self, question: str, ranked_news: list, context: str = ""
    ) -> dict:
        """Maps the user's question to the correct news item in the JSON."""
        if not ranked_news:
            return None

        prompt = "Available news list:\n"
        for n in ranked_news:
            prompt += f"ID: {n.get('id')} | Title: {n.get('title')}\n"

        prompt += f"\nUser Question: {question}\n\n"
        prompt += "Return EXCLUSIVELY the ID of the news item the question refers to. If it is a general question or not related to specific news, write NONE."

        try:
            start_time = time.time()
            response = llm_router.invoke(
                prompt=prompt,
                system_prompt="You are an ID router. Answer only with the ID or NONE.",
                preferred_model="openai/gpt-oss-120b",
            )
            latency = time.time() - start_time

            logger.info(
                "Relevant item identified",
                extra={
                    "component": "qa_agent",
                    "metrics": {"latency_ms": round(latency * 1000, 2)},
                },
            )

            resp_clean = response.strip()
            for n in ranked_news:
                if n.get("id") in resp_clean:
                    return n

        except Exception as e:
            logger.error(
                f"News identification error: {e}",
                exc_info=True,
                extra={"component": "qa_agent"},
            )

        return None

    def _fetch_live_article(self, url: str) -> str:
        """Attempts to read the original article from the web."""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                text = " ".join([p.text for p in soup.find_all("p")])
                return text[:4000]
        except Exception:
            pass
        return ""

    def _quick_web_search(self, query: str) -> str:
        """Executes a real-time background web search."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=4))
                if not results:
                    return ""
                search_context = ""
                for r in results:
                    search_context += f"- {r.get('title')}: {r.get('body')}\n"
                return search_context
        except Exception as e:
            logger.warning(f"Background web search failed: {e}")
            return ""

    def _calculate_deterministic_confidence(
        self, is_supported: bool, evidence: str, source_text: str
    ) -> float:
        """
        Calculates Composite Confidence using both Contiguous Matching and 
        Word-Level Overlap (Bag-of-Words) to survive LLM truncations.
        """
        if (
            not is_supported
            or not evidence
            or evidence.strip() == ""
            or evidence.lower() == "null"
        ):
            return 0.0


        def normalize(t: str) -> str:
            t = t.lower()
            t = re.sub(r"[’‘'`]", "'", t)
            t = re.sub(r'["“”]', '"', t)
            # Rimuove punteggiatura superflua per evitare falsi negativi sulle virgole
            t = re.sub(r'[.,;:!?()\[\]{}]', ' ', t)
            t = re.sub(r"\s+", " ", t)
            return t.strip()

        clean_evidence = normalize(evidence)
        clean_source = normalize(source_text)

        # 2. Metodo Contiguo (SequenceMatcher)
        matcher = difflib.SequenceMatcher(None, clean_evidence, clean_source)
        match = matcher.find_longest_match(0, len(clean_evidence), 0, len(clean_source))
        contiguous_ratio = match.size / max(1, len(clean_evidence))

        # 3. Metodo Word-Level Overlap (Resiliente a frasi incollate o parole omesse)
        ev_words = set(clean_evidence.split())
        src_words = set(clean_source.split())
        
        word_overlap_ratio = 0.0
        if ev_words:
            # Quante parole dell'evidenza LLM esistono davvero nel testo originale?
            common_words = ev_words.intersection(src_words)
            word_overlap_ratio = len(common_words) / len(ev_words)

        # Usiamo il ratio migliore tra i due metodi
        best_ratio = max(contiguous_ratio, word_overlap_ratio)

        # Calcolo finale
        base_weight = 0.80 if best_ratio > 0.6 else 0.40
        confidence = (0.75 * best_ratio) + (0.25 * base_weight)

        return round(confidence * 100, 2)

    def answer_question(
        self, question: str, target_item: dict, source_text: str = "", context: str = ""
    ) -> dict:
        """Handles any type of question leveraging context, web search, and mathematical confidence."""

        live_text = ""
        web_results = ""

        # 1. Scraping / Web Search
        if target_item and target_item.get("source_url"):
            live_text = self._fetch_live_article(target_item["source_url"])

        search_query = question
        if target_item:
            search_query = f"{question} {target_item.get('title')}"

        logger.info(
            f"J.A.R.V.I.S. is analyzing the request and searching the web: {search_query}"
        )
        web_results = self._quick_web_search(search_query)

        # 2. Strict Evidence Extraction Prompt
        system_prompt = """You are J.A.R.V.I.S., a strict, evidence-grounded intelligence assistant.
        GUIDELINES:
        1. Answer the user's question using ONLY the provided Source Text or Web Results.
        2. Set "is_supported" to true ONLY IF you can find the answer in the text. If not, set it to false.
        3. EVIDENCE RULE: The "evidence" field MUST be an ARRAY OF STRINGS containing the exact, verbatim substrings copied directly from the English source text. If the answer is pieced together from multiple parts of the text, extract each part as a separate string in the array. DO NOT translate or paraphrase.
        4. ANSWER RULE: Answer the user in the language of the question, maintaining an ironic, sharp, British tone, addressing the user as 'Sir'.

        You MUST output a valid JSON object strictly matching this format:
        {
            "answer": "Your conversational response based on evidence.",
            "evidence": ["Exact English sentence 1", "Exact English sentence 2"],
            "is_supported": true or false
        }"""

        # Inizializzazione obbligatoria prima di qualsiasi operazione di concatenazione (+=)
        prompt = f"USER QUESTION: {question}\n\n"
        full_context_for_validation = ""

        # Inclusione del testo del briefing originale (da source_text o context)
        base_text = source_text or context
        if base_text:
            prompt += f"--- ORIGINAL BRIEFING/CONTEXT ---\n{base_text}\n\n"
            full_context_for_validation += f"{base_text}\n"

        if target_item:
            prompt += "--- TRUSTED SOURCE ---\n"
            trusted_context = f"Title: {target_item.get('title')}\nSummary: {target_item.get('summary')}\n"
            if len(live_text) > 200:
                trusted_context += f"Extracted Text: {live_text}\n"
            prompt += trusted_context
            full_context_for_validation += trusted_context

        if web_results:
            prompt += f"\n--- UNTRUSTED WEB RESULTS ---\n{web_results}\n"
            full_context_for_validation += web_results

        try:
            start_time = time.time()
            response_json_str = llm_router.invoke(
                prompt=prompt,
                system_prompt=system_prompt,
                preferred_model="openai/gpt-oss-120b",
            )
            latency = time.time() - start_time

            clean_str = response_json_str.strip()
            if clean_str.startswith("```json"):
                clean_str = (
                    clean_str.removeprefix("```json").removesuffix("```").strip()
                )
            elif clean_str.startswith("```"):
                clean_str = clean_str.removeprefix("```").removesuffix("```").strip()

            parsed_response = json.loads(clean_str)

            is_supported = parsed_response.get("is_supported", False)
            raw_evidence = parsed_response.get("evidence", [])
            
            # Se l'LLM restituisce una stringa singola per errore, convertila in lista
            if isinstance(raw_evidence, str):
                raw_evidence = [raw_evidence]
                
            # Uniamo l'array in una singola stringa separata da puntini di sospensione per la grafica
            evidence = " [...] ".join([e.strip() for e in raw_evidence if e and e.strip() != "None"])
            if not evidence:
                evidence = ""

            logger.info(
                f"LLM Evidence check: is_supported={is_supported} | Evidence: '{evidence}'"
            )

            # 4. Mathematical Confidence Calculation
            confidence = self._calculate_deterministic_confidence(
                is_supported, evidence, full_context_for_validation
            )

            # 4. Abstention Protocol
            if not is_supported or confidence < 60.0:
                logger.warning(
                    f"Abstention triggered! LLM Confidence rejected. Score: {confidence}%"
                )
                return {
                    "answer": "I'm sorry, Sir. There is insufficient verified evidence to provide a reliable answer to that question.",
                    "evidence": None,
                    "confidence": 0.0,
                }

            # 5. Formattazione risposta
            final_answer = parsed_response.get("answer", "")
            
            logger.info(
                "Grounded Q&A Generated with Mathematical Confidence",
                extra={
                    "component": "qa_agent",
                    "metrics": {
                        "latency_ms": round(latency * 1000, 2),
                        "confidence": confidence,
                    },
                },
            )

            return {
                "answer": final_answer, # Solo testo puro
                "evidence": evidence,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(
                f"Answer generation error or JSON invalid: {e}",
                exc_info=True,
                extra={"component": "qa_agent"},
            )
            return {
                "answer": "My apologies, Sir. My cognitive circuits encountered an anomaly parsing the evidence.",
                "evidence": None,
                "confidence": 0.0,
            }
