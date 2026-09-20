import math
from typing import List

def dcg_at_k(relevances: List[int], k: int) -> float:
    """Calculates Discounted Cumulative Gain."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg

def ndcg_at_k(predicted: List[int], ideal: List[int], k: int) -> float:
    """Calculates Normalized DCG."""
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(predicted, k) / idcg

def precision_at_k(predicted: List[int], k: int, threshold: int = 50) -> float:
    """Calculates Precision@K."""
    if k == 0 or len(predicted) == 0: return 0.0
    top_k = predicted[:k]
    relevant = sum(1 for rel in top_k if rel >= threshold)
    return relevant / min(k, len(top_k))

def recall_at_k(predicted: List[int], ideal: List[int], k: int, threshold: int = 50) -> float:
    """Calculates Recall@K."""
    total_relevant = sum(1 for rel in ideal if rel >= threshold)
    if total_relevant == 0: return 0.0
    top_k = predicted[:k]
    relevant_retrieved = sum(1 for rel in top_k if rel >= threshold)
    return relevant_retrieved / total_relevant