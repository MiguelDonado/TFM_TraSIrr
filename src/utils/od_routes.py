"""
Converts the od_routes nested structure to a tidy row-per-edge format
for parquet export and downstream analysis in R.

Input
-----
{
    ("A", "B"): [["e1", "e2", "e3"],   # route 0
                 ["e1", "e4", "e5"]],  # route 1
    ("A", "C"): [["e1", "e6"]],        # route 0
}

Output (one row per edge per route)
------------------------------------
origin | dest | route_id | step | edge
A      | B    | 0        | 0    | e1
A      | B    | 0        | 1    | e2
A      | B    | 0        | 2    | e3
A      | B    | 1        | 0    | e1
...
"""

from lxml import etree


def parse_route(routes_file):
    try:
        document = routes_file
        tree = etree.parse(document)

        # Routes
        routes = tree.xpath("//route/@edges")
        edges = [route.split(" ") for route in routes]
        return edges

    except Exception:
        return None


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
