import clingo

class Solver: 
    def __init__(self, encoding_file):
        self.encoding_file = encoding_file

    # restituisco direttamente le coordinate dove piazzare i gatti 
    def solve(self, facts: list) -> list:
        ctl = clingo.Control()
        ctl.load(self.encoding_file)
        ctl.add("base", [], "\n".join(facts))
        ctl.ground([("base", [])])
        
        result = []
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                model_facts = []
                for sym in model.symbols(shown=True):
                        args = tuple(
                            arg.number if arg.type == clingo.SymbolType.Number else str(arg)
                            for arg in sym.arguments
                        )
                        model_facts.append(args)
                print(f"Model found: {model_facts}")
                
                result.append(model_facts)
        return result[0]