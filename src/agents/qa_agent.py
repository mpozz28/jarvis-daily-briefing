import logging
import requests
import time
from src.utils.observability import logger, metrics_tracker
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from src.llm_router import llm_router

logger = logging.getLogger(__name__)

class QAAgent:
    def __init__(self):
        pass

    def identify_relevant_item(self, question: str, ranked_news: list, context: str = "") -> dict:
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
                preferred_model="openai/gpt-oss-120b"
            )
            latency = time.time() - start_time
            
            # I token li calcola già il router, logghiamo solo l'evento Q&A!
            logger.info("Relevant item identified", extra={"component": "qa_agent", "metrics": {"latency_ms": round(latency * 1000, 2)}})

            resp_clean = response.strip()
            for n in ranked_news:
                if n.get('id') in resp_clean:
                    return n
                    
        except Exception as e:
            logger.error(f"News identification error: {e}", exc_info=True, extra={"component": "qa_agent"})
            
        return None

    def _fetch_live_article(self, url: str) -> str:
        """Attempts to read the original article from the web."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = " ".join([p.text for p in soup.find_all('p')])
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

    def answer_question(self, question: str, target_item: dict, source_text: str, context: str = "") -> str:
        """Handles any type of question leveraging context, web search, and logic."""
        
        live_text = ""
        web_results = ""

        # 1. If there is a referenced news item, try to read it
        if target_item and target_item.get("source_url"):
            live_text = self._fetch_live_article(target_item["source_url"])

        # 2. If the news has a paywall or the question requires external info, search the web
        search_query = question
        if target_item:
            search_query = f"{question} {target_item.get('title')}"

        logger.info(f"J.A.R.V.I.S. is analyzing the request and searching the web: {search_query}")
        web_results = self._quick_web_search(search_query)

        # 3. Flexible, intelligent prompt tailored for voice synthesis
        system_prompt = """You are J.A.R.V.I.S., the private intelligence assistant.
        You can answer any type of question: current events, logical explanations, general concepts, or complex reasoning.
        
        GUIDELINES:
        - Be natural, brilliant, and authoritative. Use your logic and the provided context or search information to formulate complete answers.
        - If a specific piece of data (like a company name) is not clear in the immediate sources but can be logically deduced or found via web results, connect it intelligently.
        - FORMATTING: Avoid complex formatting like hashtags (#) or bulleted lists with heavy asterisks. Write in a conversational, fluid, and natural manner.
        - NUMBERS AND SYMBOLS: ALWAYS use standard symbols (e.g., %, $) instead of writing the words "percent" or "dollars". Use digits for numbers.
        - Always address the user as 'Sir' and maintain an ironic, sharp, British tone.
        """

        # 4. Assemble the prompt for the LLM
        prompt = f"USER QUESTION: {question}\n\n"
        
        if target_item:
            prompt += f"--- ASSOCIATED NEWS ---\n"
            prompt += f"Title: {target_item.get('title')}\n"
            prompt += f"Summary: {target_item.get('summary')}\n"
            if len(live_text) > 200:
                prompt += f"Extracted Web Content: {live_text}\n"
        
        if web_results:
            prompt += f"\n--- LIVE WEB SUPPORTING RESULTS ---\n{web_results}\n"

        try:
            start_time = time.time()
            answer = llm_router.invoke(
                prompt=prompt,
                system_prompt=system_prompt,
                preferred_model="openai/gpt-oss-120b"
            )
            latency = time.time() - start_time
            
            logger.info("Q&A Generated", extra={"component": "qa_agent", "metrics": {"latency_ms": round(latency * 1000, 2)}})

            answer = answer.replace('##', '').replace('###', '').replace('**', '')
            return answer
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}", exc_info=True, extra={"component": "qa_agent"})
            return "My apologies, Sir. My cognitive circuits have encountered a temporary anomaly."