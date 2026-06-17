def od_routes_to_rows(od_routes: dict) -> list[dict]:
    rows = []
    for (origin, dest), routes in od_routes.items():
        for route_id, route in enumerate(routes):
            for step, edge in enumerate(route):
                rows.append(
                    {
                        "origin": origin,
                        "dest": dest,
                        "route_id": route_id,
                        "step": step,
                        "edge": edge,
                    }
                )
    return rows
