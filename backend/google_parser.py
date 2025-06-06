# google_parser.py

# --- Placeholder Logic ---
# This parser defines the GoogleQueryParser class but does not perform
# real parsing. It returns a minimal, valid AST.

from ast_nodes import QueryRootNode, TermNode

class GoogleQueryParser: # <-- FIX: Added the class definition
    def __init__(self):
        pass

    def parse(self, query_string: str) -> QueryRootNode:
        """
        Placeholder parse method.
        Returns a simple AST with the query string inside a TermNode.
        """
        if not query_string.strip():
            return QueryRootNode(query=TermNode("__EMPTY__"))

        placeholder_node = TermNode(f"Parsed from Google: '{query_string}'")
        return QueryRootNode(query=placeholder_node, settings={})