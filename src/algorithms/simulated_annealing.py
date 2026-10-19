import random
import math
from time import perf_counter
from src.model import *
from src.geometry import *
from src.moves import generate_neighbor

# SA algorithm  
def simulated_annealing(truck: Truck, packages: dict[str, Package], initial_state: State, temperature: float, cooling_rate: float, max_iterations: int):
    start = perf_counter()

    # initial state
    current_state = State(initial_state.placements.copy())
    current_value = score(truck, packages, current_state)

    best_state = State(current_state.placements.copy())
    best_value = current_value

    stagnant_iterations = 0
    stagnant_count = 0

    history = [{
        "iteration": 0,
        "current_value": current_value,
        "best_value": best_value,
        "temperature": temperature,
        "acceptance_probability": None
    }]

    # start SA main loop
    for iteration in range(1, max_iterations + 1):
        # stop if temperature is below minimum
        if temperature <= 0:
            break

        #generate neighbor state
        neighbor = generate_neighbor(truck, packages, current_state)

        probability = 0.0
        # validate neighbor state
        if neighbor.placements != current_state.placements and is_valid_placement(truck, packages, neighbor):
            neighbor_value = score(truck, packages, neighbor)
            delta = neighbor_value - current_value

            # if neighbor is better, accept it
            if delta >= 0:
                probability = 1.0
            else:
                probability = math.exp(delta / temperature)

            if random.random() < probability:
                current_state = neighbor
                current_value = neighbor_value

                # update best state
                if current_value > best_value:
                    best_state = State(current_state.placements.copy())
                    best_value = current_value
                    stagnant_iterations = 0
                else:
                    stagnant_iterations += 1

                # use max stagnation 100
                if stagnant_iterations == 100:
                    stagnant_count += 1

                history.append({
                    "iteration": iteration,
                    "current_value": current_value,
                    "best_value": best_value,
                    "temperature": temperature,
                    "acceptance_probability": probability
                })

                # cool down temperature
                temperature *= cooling_rate

                return {
                    "initial_state": State(initial_state.placements.copy()),
                    "final_state": best_state,
                    "final_value": best_value,
                    "iterations": len(history) - 1,
                    "duration_seconds": perf_counter() - start,
                    "stagnant_count": stagnant_count,
                    "history": history
                }