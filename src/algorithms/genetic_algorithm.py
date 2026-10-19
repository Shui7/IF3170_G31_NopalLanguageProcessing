from src.model import Package, Truck, Placement, State, Orientation
from src.moves import generateRandomState
from src.geometry import score, is_valid_placement
import math
import random
from time import perf_counter

def genetic_algorithm(truck: Truck, packages: dict[str, Package], initial_state: State | None = None, population_count: int = 50, iteration_count: int = 100) -> dict:
    start = perf_counter()
    
    result = State(placements={})
    isResultValid = False
    resultValue = float('-inf')
    
    # Generate initial population
    if initial_state is None:
        population = [generateRandomState(truck, packages) for _ in range(population_count)]
    else:
        population = [initial_state] + [generateRandomState(truck, packages) for _ in range(population_count - 1)]

    history = []

    values = [0.0 for _ in range(population_count)]
    total_value = 0
    initial_value = 0

    # Populate history
    for i in range(population_count):
        values[i] = score(truck, packages, population[i])
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
        # Obtain values for each state
        for i in range(population_count):
            values[i] = score(truck, packages, population[i])
            total_value += values[i]
            # Check potential valid result
            if resultValue < values[i]:
                isPotentialValid = is_valid_placement(truck, packages, population[i])
                if not isResultValid or (isResultValid and isPotentialValid):
                    result = population[i]
                    isResultValid = isPotentialValid
                    resultValue = values[i]

        # Normalize values
        min_value = min(values)
        if min_value < 0:
            for i in range(population_count):
                values[i] -= min_value
            total_value -= min_value * population_count

        # Find fitness value
        fitness = [0.0 for _ in range(population_count)]
        if total_value <= 0:
            fitness = [1/population_count for _ in range(population_count)]
        else:
            for i in range(population_count):
                fitness[i] = values[i] / total_value

        # Cross-over
        crossover: list[State] = []
        for _ in range(math.floor(population_count/2)):
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

        # If population odd, add state with highest fitness value to offspring to maintain population_count
        if population_count % 2 == 1:
            crossover.append(population[index_highest])

        # Mutation (50/50 happends)
        # for i in range(population_count):
        #     rand = random.random()
        #     if rand < 0.5:
        #         # move randomly, to be implemented
        #         # for now, remove a placement
        #         package_ids = list(crossover[i].placements)
        #         if package_ids:
        #             package_id = random.choice(package_ids)
        #             crossover[i].placements[package_id] = None

        population = crossover

        index_highest = -1
        highest_value = float('-inf')
        for i in range(population_count):
            if highest_value < values[i]:
                index_highest = i
                highest_value = values[i]
        history.append({
            "iteration": iteration + 1,
            "average_value": total_value/population_count,
            "best_value": highest_value
        })

    for i in range(population_count):
        value = score(truck, packages, population[i])
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
