def parse_limit(raw_limit) -> int:
    try:
        return max(1, min(int(raw_limit if raw_limit is not None else 5), 20))
    except ValueError as exc:
        raise ValueError("limit must be an integer") from exc