"""
Network & Asset Graph Persistence Layer.
Manages storage and relationship queries for the SOC asset topology graph.
"""

import os
import json
import logging
import networkx as nx
from soc.bootstrap import get_soc_path

logger = logging.getLogger("GraphPersistence")

GRAPH_FILE = get_soc_path("reports", "network_graph.json")


class GraphPersistenceManager:
    """Manages the serialization and deserialization of the NetworkX DiGraph."""

    @staticmethod
    def load_graph() -> nx.DiGraph:
        """Loads the saved network graph or initializes a new one."""
        if os.path.exists(GRAPH_FILE):
            try:
                with open(GRAPH_FILE, "r") as f:
                    data = json.load(f)
                    graph = nx.node_link_graph(data, directed=True)
                    logger.debug(
                        f"Loaded network graph with {graph.number_of_nodes()} nodes."
                    )
                    return graph
            except Exception as e:
                logger.error(f"Failed to load graph, starting fresh: {e}")

        # Return a new directed graph if it doesn't exist or failed to load
        return nx.DiGraph()

    @staticmethod
    def save_graph(graph: nx.DiGraph) -> None:
        """Saves the NetworkX DiGraph to JSON."""
        try:
            os.makedirs(os.path.dirname(GRAPH_FILE), exist_ok=True)
            data = nx.node_link_data(graph)
            with open(GRAPH_FILE, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved network graph with {graph.number_of_nodes()} nodes.")
        except Exception as e:
            logger.error(f"Failed to save network graph: {e}")
