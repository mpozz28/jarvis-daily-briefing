import json
import math
import os
import logging
from typing import List

# Importiamo l'agente reale che stiamo valutando
from src.agents.ranking_agent import rank_and_filter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - EVALUATOR - %(message)s')
logger = logging.getLogger(__name__)

def dcg_at_k(relevances: List[int], k: int) -> float:
    """Calcola il Discounted Cumulative Gain. Penalizza i risultati buoni se messi troppo in basso."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        # Formula standard DCG: rel_i / log2(i + 2)
        dcg += relevances[i] / math.log2(i + 2) 
    return dcg

def ndcg_at_k(predicted_relevances: List[int], ideal_relevances: List[int], k: int) -> float:
    """Calcola il Normalized DCG tra 0 e 1."""
    dcg = dcg_at_k(predicted_relevances, k)
    idcg = dcg_at_k(ideal_relevances, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def run_evaluation():
    logger.info("Avvio Ranking Evaluation...")
    
    # 1. Carica il Golden Dataset
    dataset_path = os.path.join(os.path.dirname(__file__), '../../eval/ranking_dataset.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        golden_data = json.load(f)
        
    # Mappa rapida id -> expected_relevance
    relevance_map = {item['id']: item['expected_relevance'] for item in golden_data}
    
    # Calcola il sorting ideale (quali sarebbero dovuti essere i top 3)
    ideal_order = sorted(golden_data, key=lambda x: x['expected_relevance'], reverse=True)
    ideal_relevances = [item['expected_relevance'] for item in ideal_order]
    
    logger.info(f"Dataset caricato: {len(golden_data)} articoli.")
    
    # 2. Fai processare i dati a J.A.R.V.I.S. (Nascondendo la risposta esatta)
    test_data = []
    for item in golden_data:
        test_item = item.copy()
        test_item.pop("expected_relevance", None) # Nascondiamo la risposta
        test_data.append(test_item)
        
    logger.info("Chiamata al LLM Ranking Agent in corso...")
    predicted_ranking = rank_and_filter(test_data)
    
    # 3. Estrai le relevances in base a come le ha ordinate l'LLM
    predicted_relevances = []
    logger.info("--- RISULTATI LLM RANKING ---")
    for i, item in enumerate(predicted_ranking):
        rel = relevance_map.get(item['id'], 0)
        predicted_relevances.append(rel)
        logger.info(f"{i+1}. [Rel: {rel}] {item.get('title')}")
        
    # 4. Calcola le metriche a K=3 (Valutiamo i Top 3)
    K = 3
    ndcg_score = ndcg_at_k(predicted_relevances, ideal_relevances, k=K)
    
    # 5. Output Finale
    logger.info("====================================")
    logger.info(f"🏆 METRICA NDCG@{K}: {ndcg_score:.4f} (Ideale: 1.0000)")
    logger.info("====================================")
    
    if ndcg_score > 0.85:
        logger.info("✅ TEST PASSATO: Il ranking è eccellente.")
    elif ndcg_score > 0.60:
        logger.info("⚠️ TEST INCERTO: Il ranking è discreto ma migliorabile.")
    else:
        logger.error("❌ TEST FALLITO: L'LLM sta dando priorità alle notizie sbagliate.")

if __name__ == "__main__":
    run_evaluation()