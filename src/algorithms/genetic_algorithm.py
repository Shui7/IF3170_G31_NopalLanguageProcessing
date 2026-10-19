from src.model import Package, Truck, Placement, State, Orientation
from src.moves import generateRandomState
from src.geometry import score, is_valid_placement
import math
import random

def genetic_algorithm(truck: Truck, packages: dict[str, Package], initial_state: State, population_count: int, iteration_count: int, maxList: list[float], avgList: list[float]) -> State:
    result = State(placements={})
    isResultValid = False
    resultValue = float('-inf')
    
    # Generate initial population
    population = [initial_state] + [generateRandomState(truck, packages) for _ in range(population_count - 1)]
    

    # Start iterating
    for _ in range(iteration_count):
        # Obtain values for each state
        values = [0.0 for _ in range(population_count)] 
        total_value = 0

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

        # Populate maxList and avgList
        index_highest = -1
        highest_value = float('-inf')
        for i in range(population_count):
            if highest_value < values[i]:
                index_highest = i
                highest_value = values[i]
        maxList.append(highest_value)
        avgList.append(total_value/population_count)

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

    for i in range(population_count):
        value = score(truck, packages, population[i])
        if resultValue < value:
            isPotentialValid = is_valid_placement(truck, packages, population[i])
            if not isResultValid or (isResultValid and isPotentialValid):
                result = population[i]
                isResultValid = isPotentialValid
                resultValue = value

    return result
