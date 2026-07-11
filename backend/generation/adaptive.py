from generation.sufficiency import check_sufficiency
from models.schemas import AdaptiveRetrievalResult, Chunk, RetrievalHop
from retrieval.hybrid import retrieve
from routing.router import route_query

MAX_HOPS = 2
TOP_K_PER_HOP = 5


def adaptive_retrieve(query: str) -> AdaptiveRetrievalResult:
    routing = route_query(query)

    hops: list[RetrievalHop] = []
    accumulated: dict[str, Chunk] = {}
    current_query = query

    for hop_number in range(1, MAX_HOPS + 1):
        results = retrieve(current_query, strategy=routing.strategy, top_k=TOP_K_PER_HOP)
        hop_chunks = [c for c, _ in results]
        for c in hop_chunks:
            accumulated[c.id] = c

        # Always judge sufficiency against the original question — that's what must ultimately be answered.
        sufficiency = check_sufficiency(query, list(accumulated.values()))
        hops.append(
            RetrievalHop(
                hop_number=hop_number,
                query=current_query,
                strategy=routing.strategy,
                chunks=hop_chunks,
                sufficiency=sufficiency,
            )
        )

        if sufficiency.sufficient or hop_number == MAX_HOPS:
            break
        current_query = sufficiency.reformulated_query or current_query

    return AdaptiveRetrievalResult(routing=routing, hops=hops, final_chunks=list(accumulated.values()))
