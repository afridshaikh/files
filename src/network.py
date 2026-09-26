from dataclasses import dataclass
import math
import random
import networkx as nx
import pandas as pd


@dataclass
class VirtualNetwork:
    graph: nx.Graph
    nodes: pd.DataFrame
    edges: pd.DataFrame


def build_network(cfg: dict) -> VirtualNetwork:
    rng = random.Random(cfg["seed"])
    n_zones = cfg["network"]["zones"]
    nodes_per_zone = cfg["network"]["nodes_per_zone"]
    base_elev = cfg["network"]["base_elevation_m"]
    elev_var = cfg["network"]["elevation_variation_m"]

    graph = nx.Graph()

    # Reservoir / treatment source
    graph.add_node(
        "R1",
        node_type="reservoir",
        zone=0,
        elevation_m=base_elev,
    )

    rows = [{
        "node_id": "R1",
        "node_type": "reservoir",
        "zone": 0,
        "elevation_m": base_elev,
    }]

    node_index = 1

    # Create zones as ring-like clusters with feeder connections.
    zone_nodes = {}

    for zone in range(1, n_zones + 1):
        ids = []
        for _ in range(nodes_per_zone):
            node_id = f"N{node_index:04d}"
            node_index += 1
            elevation = base_elev + rng.uniform(-elev_var, elev_var)
            graph.add_node(
                node_id,
                node_type="junction",
                zone=zone,
                elevation_m=elevation,
            )
            rows.append({
                "node_id": node_id,
                "node_type": "junction",
                "zone": zone,
                "elevation_m": elevation,
            })
            ids.append(node_id)

        zone_nodes[zone] = ids

        # Ring
        for i in range(len(ids)):
            graph.add_edge(ids[i], ids[(i + 1) % len(ids)], link_type="pipe")

        # Chords improve connectivity
        for i in range(0, len(ids) - 4, 4):
            graph.add_edge(ids[i], ids[i + 4], link_type="pipe")

    # Connect reservoir to first node of every zone.
    for zone, ids in zone_nodes.items():
        graph.add_edge("R1", ids[0], link_type="pipe")

    # Connect zones in a chain for a connected meshed topology.
    for zone in range(1, n_zones):
        graph.add_edge(zone_nodes[zone][-1], zone_nodes[zone + 1][0], link_type="pipe")

    edge_rows = []
    for idx, (u, v, attrs) in enumerate(graph.edges(data=True), start=1):
        length = rng.uniform(100, 900)
        diameter = rng.choice([100, 150, 200, 250, 300, 400])
        edge_rows.append({
            "pipe_id": f"P{idx:05d}",
            "from_node": u,
            "to_node": v,
            "length_m": round(length, 2),
            "diameter_mm": diameter,
            "roughness": round(rng.uniform(80, 140), 2),
            "link_type": attrs.get("link_type", "pipe"),
        })

    return VirtualNetwork(
        graph=graph,
        nodes=pd.DataFrame(rows),
        edges=pd.DataFrame(edge_rows),
    )
