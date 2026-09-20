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
        dcg += relevances[i] / math.log2(i + 2) 
    return dcg

def ndcg_at_k(predicted_relevances: List[int], ideal_relevances: List[int], k: int) -> float:
    """Calcola il Normalized DCG tra 0 e 1."""
    dcg = dcg_at_k(predicted_relevances, k)
    idcg = dcg_at_k(ideal_relevances, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def precision_at_k(predicted_relevances: List[int], k: int, threshold: int = 50) -> float:
    """Calcola la Precision ai primi K risultati."""
    if k == 0 or len(predicted_relevances) == 0: return 0.0
    top_k = predicted_relevances[:k]
    relevant = sum(1 for rel in top_k if rel >= threshold)
    return relevant / min(k, len(top_k))

def recall_at_k(predicted_relevances: List[int], ideal_relevances: List[int], k: int, threshold: int = 50) -> float:
    """Calcola la Recall ai primi K risultati."""
    total_relevant = sum(1 for rel in ideal_relevances if rel >= threshold)
    if total_relevant == 0: return 0.0
    top_k = predicted_relevances[:k]
    relevant_retrieved = sum(1 for rel in top_k if rel >= threshold)
    return relevant_retrieved / total_relevant

def run_evaluation():
    logger.info("Avvio Ranking Evaluation (Baseline vs Current System)...")
    
    # 1. Carica il Golden Dataset
    # Cerchiamo il dataset dove lo avevi posizionato tu in origine
    dataset_path = os.path.join(os.path.dirname(__file__), '../../eval/ranking_dataset.json')
    if not os.path.exists(dataset_path):
        logger.warning(f"File {dataset_path} non trovato. Fallback su mock locale per test della pipeline.")
        golden_data = [
            {"id": "1", "title": "Major AI Breakthrough", "area": "TECH", "expected_relevance": 95},
            {"id": "2", "title": "Market hits ATH", "area": "FINANZA", "expected_relevance": 85},
            {"id": "3", "title": "Minor App Update", "area": "TECH", "expected_relevance": 30},
            {"id": "4", "title": "Old obsolete article", "area": "MIX", "expected_relevance": 5}
        ]
    else:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
            
    # Mappa rapida id -> expected_relevance
    relevance_map = {item['id']: item['expected_relevance'] for item in golden_data}
    
    # Calcola il sorting ideale
    ideal_order = sorted(golden_data, key=lambda x: x['expected_relevance'], reverse=True)
    ideal_relevances = [item['expected_relevance'] for item in ideal_order]
    
    logger.info(f"Dataset pronto: {len(golden_data)} articoli.")
    
    # 2. BASELINE (Simuliamo l'ordinamento naturale/deterministico di base, ad es. ordine alfabetico inverso o casuale)
    # Per il benchmark consideriamo come baseline l'ordine in cui sono stati forniti
    baseline_relevances = [item['expected_relevance'] for item in golden_data]

    # 3. CURRENT SYSTEM (Fai processare i dati a J.A.R.V.I.S. nascondendo la risposta)
    test_data = []
    for item in golden_data:
        test_item = item.copy()
        test_item.pop("expected_relevance", None)
        test_data.append(test_item)
        
    logger.info("Chiamata all'Hybrid LLM Reranker in corso...")
    predicted_ranking = rank_and_filter(test_data)
    
    predicted_relevances = []
    for item in predicted_ranking:
        rel = relevance_map.get(item['id'], 0)
        predicted_relevances.append(rel)
        
    # 4. Calcolo Metriche
    K_list = [3, 5]
    threshold = 50 # Articoli con score >= 50 sono "rilevanti"
    
    metrics = {"baseline": {}, "current": {}}
    for k in K_list:
        metrics["baseline"][f"ndcg_{k}"] = ndcg_at_k(baseline_relevances, ideal_relevances, k)
        metrics["current"][f"ndcg_{k}"] = ndcg_at_k(predicted_relevances, ideal_relevances, k)
        
        metrics["baseline"][f"p_{k}"] = precision_at_k(baseline_relevances, k, threshold)
        metrics["current"][f"p_{k}"] = precision_at_k(predicted_relevances, k, threshold)
        
        metrics["baseline"][f"r_{k}"] = recall_at_k(baseline_relevances, ideal_relevances, k, threshold)
        metrics["current"][f"r_{k}"] = recall_at_k(predicted_relevances, ideal_relevances, k, threshold)

    # 5. Output Finale in stile Tabella
    logger.info("================ BENCHMARK RESULTS ================")
    logger.info("System        | NDCG@3 | NDCG@5 | P@5   | R@5   ")
    logger.info("---------------------------------------------------")
    logger.info(f"Baseline      | {metrics['baseline']['ndcg_3']:.4f} | {metrics['baseline'].get('ndcg_5', 0):.4f} | {metrics['baseline'].get('p_5', 0):.4f} | {metrics['baseline'].get('r_5', 0):.4f}")
    logger.info(f"Current (LLM) | {metrics['current']['ndcg_3']:.4f} | {metrics['current'].get('ndcg_5', 0):.4f} | {metrics['current'].get('p_5', 0):.4f} | {metrics['current'].get('r_5', 0):.4f}")
    logger.info("===================================================")

if __name__ == "__main__":
    run_evaluation()