from time import perf_counter
from src.model import Package, Truck, State
from src.geometry import is_valid_placement, score
from src.moves import generate_neighbors, generateRandomState

def steepest_ascent(truck: Truck, packages: dict[str, Package], initial_state: State | None = None, max_iterations: int | None = None) -> dict:
    if max_iterations is not None:
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
            raise TypeError("max_iterations harus berupa bilangan integer")
        if max_iterations < 0:
            raise ValueError("max_iterations harus berupa bilangan integer yang tidak negatif")

    start = perf_counter()
    # initial state
    if initial_state is None:
        initial_state = generateRandomState(truck, packages)
    if not is_valid_placement(truck, packages, initial_state):
        raise ValueError("initial_state harus memenuhi semua batasan penempatan yang telah ditetapkan")
    current_state = State(initial_state.placements.copy())
    current_value = score(truck, packages, current_state)
    initial_value = current_value

    history = [{
        "iteration": 0,
        "current_value": current_value,
        "neighbors_evaluated": 0,
        "accepted": False,
    }]

    iteration = 0
    accepted_moves = 0
    stop_reason = "max_iterations"
    while max_iterations is None or iteration < max_iterations:
        best_neighbor = None
        best_neighbor_value = float("-inf")
        neighbors_evaluated = 0
        # find the best neighbor from all valid neighbors
        for neighbor in generate_neighbors(truck, packages, current_state):
            neighbors_evaluated += 1
            neighbor_value = score(truck, packages, neighbor)
            if neighbor_value > best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = neighbor_value

        iteration += 1
        accepted = best_neighbor is not None and best_neighbor_value > current_value
        if accepted:
            current_state = best_neighbor
            current_value = best_neighbor_value
            accepted_moves += 1

        history.append({
            "iteration": iteration,
            "current_value": current_value,
            "neighbors_evaluated": neighbors_evaluated,
            "accepted": accepted,
        })

        if not accepted:
            stop_reason = "local_optimum"
            break

    return {
        "initial_state": State(initial_state.placements.copy()),
        "final_state": current_state,
        "initial_value": initial_value,
        "final_value": current_value,
        "iterations": iteration,
        "accepted_moves": accepted_moves,
        "stop_reason": stop_reason,
        "duration_seconds": perf_counter() - start,
        "history": history
    }