from time import perf_counter
from src.model import Package, Truck, State
from src.geometry import is_valid_placement
from src.moves import generate_neighbors, generateRandomState, generate_neighbor
from src.objective import score

def steepest_ascent(truck: Truck, packages: dict[str, Package], initial_state: State | None = None, max_iterations: int | None = None, objective_function=score) -> dict:
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
    current_value = objective_function(truck, packages, current_state)
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
            neighbor_value = objective_function(truck, packages, neighbor)
            if neighbor_value > best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = neighbor_value

        iteration += 1
        accepted = False
        if best_neighbor is not None and best_neighbor_value > current_value:
            current_state = best_neighbor
            current_value = best_neighbor_value
            accepted_moves += 1
            accepted = True

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

def sideways_move(truck: Truck, packages: dict[str, Package], initial_state: State | None = None, max_sideways_moves: int = 100, max_iterations: int | None = None, objective_function=score,) -> dict:
    if isinstance(max_sideways_moves, bool) or not isinstance(max_sideways_moves, int):
        raise TypeError("max_sideways_moves harus berupa bilangan integer")
    if max_sideways_moves < 0:
        raise ValueError("max_sideways_moves harus berupa bilangan integer yang tidak negatif")
    if max_iterations is not None:
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
            raise TypeError("max_iterations harus berupa bilangan integer")
        if max_iterations < 0:
            raise ValueError("max_iterations harus berupa bilangan integer yang tidak negatif")

    start = perf_counter()
    if initial_state is None:
        initial_state = generateRandomState(truck, packages)
    if not is_valid_placement(truck, packages, initial_state):
        raise ValueError("initial_state harus memenuhi semua batasan penempatan yang telah ditetapkan")

    current_state = State(initial_state.placements.copy())
    current_value = objective_function(truck, packages, current_state)
    initial_value = current_value
    iteration = 0
    accepted_moves = 0
    sideways_moves = 0
    stop_reason = "max_iterations"
    history = [{
        "iteration": 0,
        "current_value": current_value,
        "neighbors_evaluated": 0,
        "accepted": False,
        "is_sideways": False,
        "sideways_moves": 0,
    }]

    while max_iterations is None or iteration < max_iterations:
        best_neighbor = None
        best_neighbor_value = float("-inf")
        neighbors_evaluated = 0
        for neighbor in generate_neighbors(truck, packages, current_state):
            neighbors_evaluated += 1
            neighbor_value = objective_function(truck, packages, neighbor)
            if neighbor_value > best_neighbor_value:
                best_neighbor = neighbor
                best_neighbor_value = neighbor_value

        iteration += 1
        accepted = False
        is_sideways = False
        if best_neighbor is None or best_neighbor_value < current_value:
            stop_reason = "local_optimum"
        elif best_neighbor_value == current_value and sideways_moves >= max_sideways_moves:
            stop_reason = "max_sideways_moves"
        else:
            is_sideways = best_neighbor_value == current_value
            current_state = best_neighbor
            current_value = best_neighbor_value
            accepted = True
            accepted_moves += 1
            if is_sideways:
                sideways_moves += 1

        history.append({
            "iteration": iteration,
            "current_value": current_value,
            "neighbors_evaluated": neighbors_evaluated,
            "accepted": accepted,
            "is_sideways": is_sideways,
            "sideways_moves": sideways_moves,
        })

        if not accepted:
            break
        if is_sideways and sideways_moves >= max_sideways_moves:
            stop_reason = "max_sideways_moves"
            break

    return {
        "initial_state": State(initial_state.placements.copy()),
        "final_state": current_state,
        "initial_value": initial_value,
        "final_value": current_value,
        "iterations": iteration,
        "accepted_moves": accepted_moves,
        "sideways_moves": sideways_moves,
        "max_sideways_moves": max_sideways_moves,
        "stop_reason": stop_reason,
        "duration_seconds": perf_counter() - start,
        "history": history,
    }


def random_restart(truck: Truck, packages: dict[str, Package],initial_state: State | None = None, max_restarts: int = 10,max_iterations: int | None = None, objective_function=score,) -> dict:
    if isinstance(max_restarts, bool) or not isinstance(max_restarts, int):
        raise TypeError("max_restarts harus berupa bilangan integer")
    if max_restarts < 0:
        raise ValueError("max_restarts harus berupa bilangan integer yang tidak negatif")
    if max_iterations is not None:
        if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
            raise TypeError("max_iterations harus berupa bilangan integer")
        if max_iterations < 0:
            raise ValueError("max_iterations harus berupa bilangan integer yang tidak negatif")

    start = perf_counter()
    runs = []
    history = []
    iterations_per_restart = []
    total_iterations = 0
    accepted_moves = 0
    best_state = None
    best_value = float("-inf")
    best_restart = 0
    best_value_so_far = float("-inf")

    for restart in range(max_restarts + 1):
        run_initial_state = initial_state if restart == 0 else None
        result = steepest_ascent(truck, packages, run_initial_state, max_iterations, objective_function)
        runs.append({"restart": restart, **result})
        iterations_per_restart.append(result["iterations"])

        if best_state is None or result["final_value"] > best_value:
            best_state = State(result["final_state"].placements.copy())
            best_value = result["final_value"]
            best_restart = restart

        for record in result["history"]:
            best_value_so_far = max(best_value_so_far, record["current_value"])
            history.append({
                **record,
                "iteration": total_iterations + record["iteration"],
                "iteration_in_restart": record["iteration"],
                "restart": restart,
                "current_value": best_value_so_far,
            })

        total_iterations += result["iterations"]
        accepted_moves += result["accepted_moves"]

    return {
        "initial_state": State(runs[0]["initial_state"].placements.copy()),
        "final_state": best_state,
        "initial_value": runs[0]["initial_value"],
        "final_value": best_value,
        "iterations": total_iterations,
        "accepted_moves": accepted_moves,
        "restarts": len(runs) - 1,
        "max_restarts": max_restarts,
        "iterations_per_restart": iterations_per_restart,
        "best_restart": best_restart,
        "stop_reason": "max_restarts",
        "duration_seconds": perf_counter() - start,
        "history": history,
        "runs": runs,
    }

def stochastic(truck: Truck, packages: dict[str, Package], initial_state: State | None = None, *, max_iterations: int, objective_function=score, ) -> dict:
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise TypeError("max_iterations harus berupa bilangan integer")
    if max_iterations < 0:
        raise ValueError("max_iterations harus berupa bilangan integer yang tidak negatif")

    start = perf_counter()
    if initial_state is None:
        initial_state = generateRandomState(truck, packages)
    if not is_valid_placement(truck, packages, initial_state):
        raise ValueError("initial_state harus memenuhi semua constraint placement yang telah ditetapkan")

    current_state = State(initial_state.placements.copy())
    current_value = objective_function(truck, packages, current_state)
    initial_value = current_value
    accepted_moves = 0
    history = [{
        "iteration": 0,
        "current_value": current_value,
        "neighbors_evaluated": 0,
        "accepted": False,
    }]

    for iteration in range(1, max_iterations + 1):
        neighbor = generate_neighbor(truck, packages, current_state)
        accepted = False
        neighbors_evaluated = 0

        if neighbor != current_state and is_valid_placement(truck, packages, neighbor):
            neighbors_evaluated = 1
            neighbor_value = objective_function(truck, packages, neighbor)
            if neighbor_value > current_value:
                current_state = neighbor
                current_value = neighbor_value
                accepted = True
                accepted_moves += 1

        history.append({
            "iteration": iteration,
            "current_value": current_value,
            "neighbors_evaluated": neighbors_evaluated,
            "accepted": accepted,
        })

    return {
        "initial_state": State(initial_state.placements.copy()),
        "final_state": current_state,
        "initial_value": initial_value,
        "final_value": current_value,
        "iterations": max_iterations,
        "accepted_moves": accepted_moves,
        "stop_reason": "max_iterations",
        "duration_seconds": perf_counter() - start,
        "history": history,
    }