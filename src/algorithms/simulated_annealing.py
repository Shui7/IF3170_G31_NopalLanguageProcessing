import random
import math
from time import perf_counter
from src.model import *
from src.geometry import is_valid_placement
from src.moves import generate_neighbor
from src.objective import score

# SA algorithm  
def simulated_annealing(truck: Truck, packages: dict[str, Package], initial_state: State, temperature: float, cooling_rate: float, max_iterations: int, objective_function=score):
    start = perf_counter()

    # initial state
    current_state = State(initial_state.placements.copy())
    current_value = objective_function(truck, packages, current_state)

    best_state = State(current_state.placements.copy())
    best_value = current_value

    stagnant_iterations = 0
    stagnant_count = 0

    history = [{
        "iteration": 0,
        "current_value": current_value,
        "best_value": best_value,
        "temperature": temperature,
        "delta": None,
        "exp_delta_over_temp": None,
        "acceptance_probability": None,
        "accepted": False,
    }]

    # start SA main loop
    for iteration in range(1, max_iterations + 1):
        # stop if temperature is below minimum
        if temperature <= 0:
            break

        #generate neighbor state
        neighbor = generate_neighbor(truck, packages, current_state)

        delta = None
        exp_delta_over_temp = None
        probability = None
        accepted = False

        # validate neighbor state
        if neighbor.placements != current_state.placements: 
            if is_valid_placement(truck, packages, neighbor):
                neighbor_value = objective_function(truck, packages, neighbor)
                delta = neighbor_value - current_value
                exponent = delta / temperature
                # Limit the exponent to keep the value finite for plotting.
                exp_delta_over_temp = math.exp(min(exponent, 700.0))

                # if neighbor is better, accept it
                probability = min(1.0, exp_delta_over_temp)

                accepted = random.random() < probability
                if accepted:
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
            "delta": delta,
            "exp_delta_over_temp": exp_delta_over_temp,
            "acceptance_probability": probability,
            "accepted": accepted,
        })

        # cool down temperature
        temperature *= cooling_rate

    plot_data = {
        "objective": {
            "iterations": [],
            "current": [],
            "best": [],
        },
        "temperature": {
            "iterations": [],
            "values": [],
        },
        "acceptance_probability": {
            "iterations": [],
            "values": [],
        },
        "exp_delta_over_temp": {
            "iterations": [],
            "values": [],
        },
    }

    for record in history:
        iteration = record["iteration"]

        plot_data["objective"]["iterations"].append(iteration)
        plot_data["objective"]["current"].append(record["current_value"])
        plot_data["objective"]["best"].append(record["best_value"])

        plot_data["temperature"]["iterations"].append(iteration)
        plot_data["temperature"]["values"].append(record["temperature"])

        if record["acceptance_probability"] is not None:
            plot_data["acceptance_probability"]["iterations"].append(iteration)
            plot_data["acceptance_probability"]["values"].append(
                record["acceptance_probability"]
            )

        if record["exp_delta_over_temp"] is not None:
            plot_data["exp_delta_over_temp"]["iterations"].append(iteration)
            plot_data["exp_delta_over_temp"]["values"].append(
                record["exp_delta_over_temp"]
            )

    return {
        "initial_state": State(initial_state.placements.copy()),
        "final_state": best_state,
        "final_value": best_value,
        "iterations": len(history) - 1,
        "duration_seconds": perf_counter() - start,
        "stagnant_count": stagnant_count,
        "history": history,
        "plot_data": plot_data,
    }
