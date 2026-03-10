from thefuzz import fuzz, process

from src.models import Guest, SearchResult


def search_guests(query: str, guests: list[Guest], limit: int = 5) -> list[SearchResult]:
    """Fuzzy search guests by name, email, and company."""
    if not query or len(query) < 2:
        return []

    scored: dict[str, float] = {}

    # Score against full name (highest weight)
    name_map = {g.api_id: g.name for g in guests}
    name_results = process.extract(
        query, name_map, scorer=fuzz.WRatio, limit=limit * 2
    )
    for name, score, api_id in name_results:
        scored[api_id] = max(scored.get(api_id, 0), score)

    # Score against first name
    first_map = {g.api_id: g.first_name for g in guests if g.first_name}
    first_results = process.extract(
        query, first_map, scorer=fuzz.WRatio, limit=limit * 2
    )
    for name, score, api_id in first_results:
        scored[api_id] = max(scored.get(api_id, 0), score * 0.9)

    # Score against last name
    last_map = {g.api_id: g.last_name for g in guests if g.last_name}
    last_results = process.extract(
        query, last_map, scorer=fuzz.WRatio, limit=limit * 2
    )
    for name, score, api_id in last_results:
        scored[api_id] = max(scored.get(api_id, 0), score * 0.9)

    # Score against email prefix (before @)
    email_map = {
        g.api_id: g.email.split("@")[0]
        for g in guests
        if g.email and "@" in g.email
    }
    email_results = process.extract(
        query, email_map, scorer=fuzz.WRatio, limit=limit * 2
    )
    for email, score, api_id in email_results:
        scored[api_id] = max(scored.get(api_id, 0), score * 0.7)

    # Filter by minimum score and sort
    guest_map = {g.api_id: g for g in guests}
    results = []
    for api_id, score in sorted(scored.items(), key=lambda x: -x[1]):
        if score < 50:
            continue
        g = guest_map[api_id]
        results.append(
            SearchResult(
                api_id=g.api_id,
                name=g.name,
                first_name=g.first_name,
                last_name=g.last_name,
                company=g.company,
                job_title=g.job_title,
                match_score=round(score, 1),
                already_checked_in=g.checked_in_at is not None,
                checked_in_at=g.checked_in_at,
            )
        )
        if len(results) >= limit:
            break

    return results
