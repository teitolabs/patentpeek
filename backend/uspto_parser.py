# uspto_parser.py

# --- Placeholder Logic ---
# This parser defines the USPTOQueryParser class but does not perform
# real parsing. It returns a minimal, valid AST.

from ast_nodes import QueryRootNode, TermNode

class USPTOQueryParser: # <-- FIX: Added the class definition
    def __init__(self):
        pass

    def parse(self, query_string: str) -> QueryRootNode:
        """
        Placeholder parse method.
        Returns a simple AST with the query string inside a TermNode.
        """
        if not query_string.strip():
            return QueryRootNode(query=TermNode("__EMPTY__"))
        
        placeholder_node = TermNode(f"Parsed from USPTO: '{query_string}'")
        return QueryRootNode(query=placeholder_node, settings={})