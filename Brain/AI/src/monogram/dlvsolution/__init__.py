"""
Monogram DLV Solution module.
Registers predicates and initializes ASP solver.
"""

from languages.asp.asp_mapper import ASPMapper
from AI.src.monogram.dlvsolution.helpers import Cell, Hint, GridSize, Action

# Register all predicates with the ASP mapper
# This tells the framework how to parse/serialize these objects
ASPMapper.get_instance().register_class(Cell)
ASPMapper.get_instance().register_class(Hint)
ASPMapper.get_instance().register_class(GridSize)
ASPMapper.get_instance().register_class(Action)

print("[Monogram DLVSolution] Predicates registered with ASPMapper")