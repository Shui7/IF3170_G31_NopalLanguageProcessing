from src.model import Package, Truck, Placement, State, Orientation
from src.moves import generateRandomState, generate_neighbor
from src.geometry import is_valid_placement
from src.objective import score
import random
from time import perf_counter

def genetic_algorithm(truck: Truck, packages: dict[str, Package], initial_state: State | None = None, population_count: int = 50, iteration_count: int = 100, objective_function=score) -> dict:
    start = perf_counter()

    result = State(placements={})
    isResultValid = False
    resultValue = float('-inf')

    # Generate initial population
    if initial_state is None:
        population = [generateRandomState(truck, packages) for _ in range(population_count)]
    else:
        if not is_valid_placement(truck, packages, initial_state):
            raise ValueError("initial_state harus memenuhi semua batasan penempatan yang telah ditetapkan")
        population = [initial_state] + [generateRandomState(truck, packages) for _ in range(population_count - 1)]

    history = []

    values = [0.0 for _ in range(population_count)]
    total_value = 0
    initial_value = 0

    # Populate history
    for i in range(population_count):
        values[i] = objective_function(truck, packages, population[i])
        if i == 0:
            initial_value = values[i]
        total_value += values[i]
    index_highest = -1
    highest_value = float('-inf')
    for i in range(population_count):
        if highest_value < values[i]:
            index_highest = i
            highest_value = values[i]
    history.append({
        "iteration": 0,
        "average_value": total_value/population_count,
        "best_value": highest_value
    })

    # Start iterating
    for iteration in range(iteration_count):
        total_value = 0
        # Obtain values for each state
        for i in range(population_count):
            values[i] = objective_function(truck, packages, population[i])
            total_value += values[i]
            # Check potential valid result
            if resultValue < values[i]:
                isPotentialValid = is_valid_placement(truck, packages, population[i])
                if not isResultValid or (isResultValid and isPotentialValid):
                    result = population[i]
                    isResultValid = isPotentialValid
                    resultValue = values[i]

        # Normalize values
        normalized_values = []
        normalized_total_value = 0
        min_value = min(values)
        if min_value < 0:
            for i in range(population_count):
                normalized_values.append(values[i] - min_value)
            normalized_total_value = total_value - min_value * population_count

        # Find fitness value
        fitness = [0.0 for _ in range(population_count)]
        if normalized_total_value <= 0:
            fitness = [1/population_count for _ in range(population_count)]
        else:
            for i in range(population_count):
                fitness[i] = normalized_values[i] / normalized_total_value

        # Cross-over
        crossover: list[State] = []
        offspring_count = population_count * 3 // 4 # Will generate only 75% of population
        crossover_count = offspring_count // 2
        for _ in range(crossover_count):
            offsprings: list[State] = [State(placements={}), State(placements={})]

            # Pick 2 parents from population with weight from fitness value
            parents = random.choices(population, fitness, k=2)

            # Randomize crossover, 50/50 chance to pick either for each package placement
            for package_id, placement in parents[0].placements.items():
                rand = random.random()
                if rand <= 0.5:
                    offsprings[0].placements[package_id] = placement
                    offsprings[1].placements[package_id] = parents[1].placements[package_id]
                else:
                    offsprings[0].placements[package_id] = parents[1].placements[package_id]
                    offsprings[1].placements[package_id] = placement

            crossover += offsprings

        # Populate crossover with highest valued states (25% elitism)
        elite_count = population_count - len(crossover)
        ranked_indices = sorted(
            range(population_count),
            key=lambda index: values[index],
            reverse=True,
        )
        for index in ranked_indices[:elite_count]:
            crossover.append(population[index])

        # Mutation (50/50 happens to each state that is invalid, will replace state to its random neighbor)
        for i in range(population_count):
            if not is_valid_placement(truck, packages, crossover[i]) and random.random() < 0.5:
                crossover[i] = generate_neighbor(truck, packages, crossover[i])

        population = crossover

        next_values = [
            objective_function(truck, packages, state)
            for state in population
        ]
        history.append({
            "iteration": iteration + 1,
            "average_value": sum(next_values)/population_count,
            "best_value": max(next_values)
        })

    for i in range(population_count):
        value = objective_function(truck, packages, population[i])
        if resultValue < value:
            isPotentialValid = is_valid_placement(truck, packages, population[i])
            if not isResultValid or (isResultValid and isPotentialValid):
                result = population[i]
                isResultValid = isPotentialValid
                resultValue = value

    return {
        "initial_state": initial_state,
        "final_state": result,
        "initial_value": initial_value,
        "final_value": resultValue,
        "iterations": iteration_count,
        "duration_seconds": perf_counter() - start,
        "population_count": population_count,
        "history": history,
    }
