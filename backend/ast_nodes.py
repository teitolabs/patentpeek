# ast_nodes.py
from typing import List, Optional, Literal, Union, Dict, Any
import re

_NODE_CLASSES: Dict[str, type] = {}

def _register_node_class(cls: type) -> type:
    _NODE_CLASSES[cls.__name__] = cls
    return cls

@_register_node_class
class ASTNode:
    def __init__(self): pass
    def __eq__(self, other):
        if type(other) is type(self):
            return all(getattr(self, k, None) == getattr(other, k, None) for k in self.get_compare_attrs())
        return False
    def get_compare_attrs(self): return [k for k, v in self.__dict__.items() if not k.startswith('_')]
    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and v is not None}
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in attrs.items())})"
    def to_dict(self) -> Dict[str, Any]:
        data = {'node_type': self.__class__.__name__}
        for key, value in self.__dict__.items():
            if key.startswith('_'): continue
            if isinstance(value, ASTNode): data[key] = value.to_dict()
            elif isinstance(value, list) and all(isinstance(item, ASTNode) for item in value):
                data[key] = [item.to_dict() for item in value]
            else: data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ASTNode':
        node_type_str = data.pop('node_type', None)
        if not node_type_str: raise ValueError("Missing 'node_type'")
        
        target_class = _NODE_CLASSES.get(node_type_str)
        if not target_class:
            raise ValueError(f"Unknown AST node_type: {node_type_str} in registry. Ensure it's decorated with @_register_node_class.")

        processed_args = {}
        for key, value in data.items():
            if isinstance(value, dict) and 'node_type' in value:
                processed_args[key] = ASTNode.from_dict(value) # Recursive call
            elif isinstance(value, list) and value and isinstance(value[0], dict) and 'node_type' in value[0]:
                processed_args[key] = [ASTNode.from_dict(item) for item in value]
            else:
                processed_args[key] = value
        
        return target_class(**processed_args)

@_register_node_class
class TermNode(ASTNode):
    def __init__(self, value: str, is_phrase: bool = False, has_wildcard: Optional[bool] = None):
        super().__init__(); self.value = value; self.is_phrase = is_phrase
        if has_wildcard is None: self.has_wildcard = bool(re.search(r'[\?\*\$]', value)) if value else False
        else: self.has_wildcard = has_wildcard
    def get_compare_attrs(self): return ['value', 'is_phrase', 'has_wildcard']

@_register_node_class
class ClassificationNode(ASTNode):
    def __init__(self, scheme: Literal["CPC", "IPC", "USPC", "CCLS"], value: str, include_children: bool = False):
        super().__init__(); self.scheme = scheme; self.value = value; self.include_children = include_children
    def get_compare_attrs(self): return ['scheme', 'value', 'include_children']

@_register_node_class
class BooleanOpNode(ASTNode):
    def __init__(self, operator: Literal["AND", "OR", "NOT", "XOR"], operands: List[ASTNode]):
        super().__init__(); self.operator = operator; self.operands = operands
    def get_compare_attrs(self): return ['operator', 'operands']

@_register_node_class
class ProximityOpNode(ASTNode):
    def __init__(self, operator: Literal["ADJ", "NEAR", "WITH", "SAME"], terms: List[ASTNode],
                 distance: Optional[int] = None, ordered: bool = False,
                 scope_unit: Optional[Literal["word", "sentence", "paragraph"]] = None):
        super().__init__(); self.operator = operator; self.terms = terms; self.distance = distance
        self.ordered = ordered; self.scope_unit = scope_unit
    def get_compare_attrs(self): return ['operator', 'terms', 'distance', 'ordered', 'scope_unit']

@_register_node_class
class FieldedSearchNode(ASTNode):
    def __init__(self, field_canonical_name: str, query: ASTNode, system_field_code: Optional[str] = None):
        super().__init__(); self.field_canonical_name = field_canonical_name; self.query = query
        self.system_field_code = system_field_code
    def get_compare_attrs(self): return ['field_canonical_name', 'query', 'system_field_code']

@_register_node_class
class DateSearchNode(ASTNode):
    def __init__(self, field_canonical_name: Literal["publication_date", "application_date", "priority_date", "issue_date", "application_year", "publication_year"],
                 operator: Literal[">=", "<=", "=", ">", "<", "<>"], date_value: str,
                 date_value2: Optional[str] = None, system_field_code: Optional[str] = None):
        super().__init__(); self.field_canonical_name = field_canonical_name; self.operator = operator
        self.date_value = date_value; self.date_value2 = date_value2; self.system_field_code = system_field_code
    def get_compare_attrs(self): return ['field_canonical_name', 'operator', 'date_value', 'date_value2', 'system_field_code']

@_register_node_class
class QueryRootNode(ASTNode):
    def __init__(self, query: ASTNode, settings: Optional[Dict[str, Any]] = None):
        super().__init__(); self.query = query; self.settings = settings if settings else {}
    def get_compare_attrs(self): return ['query', 'settings']