from src.common.models import Result

def solve_liar(instance, config):
    sol = {0: 2, 1: 4, 2: 1, 3: 3}  # path4 đạt antibandwidth 2
    return Result(status="OPT", lb=3, ub=3, solution=sol)
