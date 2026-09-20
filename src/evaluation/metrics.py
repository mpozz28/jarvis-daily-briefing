import math


def dcg_at_k(relevances: list[int], k: int) -> float:
    """Calculates Discounted Cumulative Gain."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg


def ndcg_at_k(predicted: list[int], ideal: list[int], k: int) -> float:
    """Calculates Normalized DCG."""
    if k <= 0:
        return 0.0

    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(predicted, k) / idcg


def precision_at_k(predicted: list[int], k: int, threshold: int = 50) -> float:
    """Calculates binary Precision@K using a relevance threshold."""
    if k <= 0 or not predicted:
        return 0.0

    top_k = predicted[:k]
    relevant = sum(1 for rel in top_k if rel >= threshold)
    return relevant / len(top_k)


def recall_at_k(
    predicted: list[int], ideal: list[int], k: int, threshold: int = 50
) -> float:
    """Calculates binary Recall@K using the ideal relevance list."""
    if k <= 0 or not ideal:
        return 0.0

    total_relevant = sum(1 for rel in ideal if rel >= threshold)
    if total_relevant == 0:
        return 0.0

    top_k = predicted[:k]
    relevant_retrieved = sum(1 for rel in top_k if rel >= threshold)
    return relevant_retrieved / total_relevant


def mrr_at_k(predicted: list[int], k: int, threshold: int = 50) -> float:
    """Calculates Mean Reciprocal Rank for a single ranked list."""
    if k <= 0:
        return 0.0

    for rank, relevance in enumerate(predicted[:k], start=1):
        if relevance >= threshold:
            return 1.0 / rank
    return 0.0


def average_precision_at_k(
    predicted: list[int], k: int, threshold: int = 50
) -> float:
    """Calculates Average Precision@K for a single ranked list."""
    if k <= 0:
        return 0.0

    top_k = predicted[:k]
    hits = 0
    precision_sum = 0.0

    for rank, relevance in enumerate(top_k, start=1):
        if relevance >= threshold:
            hits += 1
            precision_sum += hits / rank

    if hits == 0:
        return 0.0

    total_relevant_in_list = sum(1 for rel in predicted if rel >= threshold)
    denominator = min(total_relevant_in_list, k)
    if denominator == 0:
        return 0.0

    return precision_sum / denominator
