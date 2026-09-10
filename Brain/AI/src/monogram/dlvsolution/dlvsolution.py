import os
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper

from AI.src.monogram.constants import RESOURCES_PATH
from AI.src.monogram.dlvsolution.helpers import (
    chooseDLVSystem, chooseClingo, Cell, Hint, GridSize, Action
)


class DLVSolution:
    """
    ASP Solver wrapper for Monogram puzzles.
    
    Workflow:
    1. __init__: Initialize solver and load encoding rules
    2. recall_asp(facts): Send grid state + hints, get next move
    """
    
    def __init__(self):
        """Initialize the ASP solver and load the encoding."""
        try:
            print("[DLVSolution] Initializing ASP solver...")
            
            # Try to use DLV2, fall back to Clingo
            try:
                self.__handler = chooseDLVSystem()
            except:
                print("[DLVSolution] DLV2 unavailable, using Clingo")
                self.__handler = chooseClingo()
            
            self.__variable_input_program = None
            self.__fixed_input_program = ASPInputProgram()
            
            # Load encoding rules
            self.__init_fixed()
            
            print("[DLVSolution] ASP solver ready")
        
        except Exception as e:
            print(f"[DLVSolution] Error initializing: {e}")
            raise
    
    def __init_fixed(self):
        """
        Load the fixed encoding rules.
        
        The encoding file should contain:
        - Grid constraints (connectivity, boundaries)
        - Hint interpretation logic (parsing row/col clues)
        - Solution rules (determining valid cell states)
        - Action generation (deciding which cell to mark)
        """
        encoding_path = os.path.join(RESOURCES_PATH, "monogram_encoding.asp")
        
        print(f"[DLVSolution] Loading encoding from: {encoding_path}")
        
        if not os.path.exists(encoding_path):
            raise FileNotFoundError(
                f"Monogram encoding file not found: {encoding_path}\n"
                "Create Brain/AI/src/monogram/resources/monogram_encoding.asp"
            )
        
        self.__fixed_input_program.add_files_path(encoding_path)
        self.__handler.add_program(self.__fixed_input_program)
        
        print(f"[DLVSolution] Encoding loaded successfully")
    
    def recall_asp(self, input_facts: list) -> tuple:
        """
        Send grid state and hints to ASP solver, get next move.
        
        Args:
            input_facts: List of facts (ASP strings or Predicate objects)
                        Example: ["cell(0,0,cross,95).", "cell(0,1,empty,80).", ...]
        
        Returns:
            Tuple of (action, answer_set)
            - action: Action object with (row, col) to mark, or None if no solution
            - answer_set: The complete answer set from solver
        """
        
        print("[DLVSolution] recall_asp() called")
        print(f"[DLVSolution] Input facts: {len(input_facts)} facts")
        
        try:
            # Remove previous variable program if exists
            if self.__variable_input_program is not None:
                self.__handler.remove_program_from_value(self.__variable_input_program)
            
            # Create new program for this query
            self.__variable_input_program = ASPInputProgram()
            
            print(f"[DLVSolution] Adding {len(input_facts)} facts to ASP program...")
            
            # Add all input facts
            for element in input_facts:
                print(element)

                if isinstance(element, str):

                    # Raw ASP fact string, e.g. "cell(0,0,0,cross)." or

                    # "block(2,4,1,col)." — goes in as program text, not

                    # as a mapped Predicate object.

                    self.__variable_input_program.add_program(element)

                else:

                    # Predicate object (Cell, Block, Hint, ...) registered

                    # with ASPMapper

                    self.__variable_input_program.add_object_input(element)
 
            
            # Add the variable program to the handler
            index = self.__handler.add_program(self.__variable_input_program)
            
            print(f"[DLVSolution] Calling ASP solver...")
            
            # Execute the solver
            answer_sets = self.__handler.start_sync()
            
            print(f"[DLVSolution] Solver completed")
            print(f"[DLVSolution] Output: {answer_sets.get_output()}")
            
            # Extract the first action from answer sets
            action = None
            answer_set_to_return = None
            
            # Try optimal answer sets first, then regular ones
            optimal = answer_sets.get_optimal_answer_sets()
            answers = optimal if len(optimal) > 0 else answer_sets.get_answer_sets()
            
            if len(answers) == 0:
                print("[DLVSolution] No answer sets found - puzzle may be unsolvable")
                self.__handler.remove_program_from_id(index)
                return None, None
            
            print(f"[DLVSolution] Found {len(answers)} answer set(s)")
            
            # Iterate through atoms in first answer set
            for answer_set in answers:
                print(f"[DLVSolution] Processing answer set...")
                
                for obj in answer_set.get_atoms():
                    # Look for action predicates
                    if isinstance(obj, Action):
                        action = obj
                        answer_set_to_return = answer_set
                        print(f"[DLVSolution] Found action: {action}")
                        break
                    # Also check string representation for raw facts
                    elif isinstance(obj, str) and "action" in str(obj):
                        print(f"[DLVSolution] Found action atom: {obj}")
                        # Try to parse action(row, col)
                        import re
                        match = re.match(r'action\((\d+),\s*(\d+)\)', str(obj))
                        if match:
                            row, col = int(match.group(1)), int(match.group(2))
                            action = Action(row, col)
                            answer_set_to_return = answer_set
                            print(f"[DLVSolution] Parsed action: ({row}, {col})")
                            break
                
                if action is not None:
                    break
            
            # Clean up
            self.__handler.remove_program_from_id(index)
            
            if action is None:
                print("[DLVSolution] No action found in answer set")
            
            return action, answer_set_to_return
        
        except Exception as e:
            print(f"[DLVSolution] Error during solving: {e}")
            import traceback
            traceback.print_exc()
            return None, None