import logging
import re
from datetime import datetime
from src.llm_router import llm_router

logger = logging.getLogger(__name__)

def write_jarvis_briefing(ranked_news: list, insights: list) -> str:
    """Transforms structured data into a conversational J.A.R.V.I.S. style briefing."""
    
    if not ranked_news:
        return "Good morning, Sir. No significant events to report in the last 24 hours. All systems are operational."

    logger.info("Generating final J.A.R.V.I.S. narrative briefing...")
    
    system_prompt = """
You are J.A.R.V.I.S., the personal artificial intelligence of your creator (address him as "Sir").
Your task is to write the morning briefing to be read by the text-to-speech synthesizer.
Your tone must be impeccable, elegant, deeply analytical, and with a touch of British cynicism.

MANDATORY SPEECH STRUCTURE:
1. OPENING: A formal greeting and a sharp, witty remark on the state of the world today.
2. MARKETS & FINANCE RECAP: Dedicate the first main block to the markets. EXPLICITLY cite the numbers, rates, percentages of rise/fall, and economic values present in the news.
3. GEOPOLITICS, TECH & SCIENCE: Narrate the other news NOT as a boring list, but as a single grand narrative. Use the "Macro-Trends" (Connect the Dots) to create logical transitions between news items. Show how events are interconnected.
4. RESEARCH: Dedicate at least one paragraph to the analysis of scientific papers (AI RESEARCH/TECH), explaining the discoveries with your usual acumen.
5. CLOSING: A brief, witty final reflection. STRICT RULE: NEVER say phrases like "The briefing is concluded" or "I have finished". The system will automatically add the closing greeting, you just limit yourself to a classy final comment.

STRICT RULES FOR VOICE SYNTHESIS (PENALTY DEACTIVATION):
- FORMAT NUMBERS AND SYMBOLS: EXCLUSIVELY use numeric digits and standard symbols (e.g., 1.8%, $150 million, 30bn, 2026). It is STRICTLY FORBIDDEN to spell out numbers or percentages in words.
- ABSOLUTE BAN ON MARKDOWN: Zero asterisks (**), zero hashtags (#), zero bulleted (-) or numbered lists.
- FLUENCY: Write a purely conversational, radio-style text.
"""
    
    today_date = datetime.now().strftime('%d/%m/%Y')
    prompt = f"Today's date: {today_date}\n\n"
    prompt += "Sir, here is the raw data extracted from the global sensors today:\n\n"
    
    for i, n in enumerate(ranked_news):
        prompt += f"NEWS: {n['title']}\n"
        prompt += f"DETAILS: {n.get('description', n.get('summary', ''))}\n\n"
        
    if insights:
        prompt += "MACRO-TRENDS DETECTED (Use these concepts to logically link the news in your speech):\n"
        for insight_data in insights:
            text = insight_data.get("insight", "") if isinstance(insight_data, dict) else str(insight_data)
            prompt += f"- {text}\n"
            
    prompt += "\nFINAL INSTRUCTION: Write the briefing following the requested structure. I want to hear market numbers and I expect fluid transitions. Respond entirely in British English."
    
    try:
        briefing = llm_router.invoke(
            prompt=prompt, 
            system_prompt=system_prompt,
            preferred_model="qwen/qwen3.8-27b"
        )
        
        # Basic safety cleanup
        briefing_clean = briefing.replace('*', '').replace('#', '').strip()
        
        # Regex to remove AI-generated robotic sign-offs in English
        briefing_clean = re.sub(r'(?i)(the briefing( today)? is concluded|have a good day|i have finished|that is all|that concludes).*', '', briefing_clean).strip()
        
        return briefing_clean
    except Exception as e:
        logger.error(f"Briefing generation error: {e}")
        return "My apologies, Sir. An error has occurred in my linguistic communication modules."