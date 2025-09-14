import random
import numpy as np
from deap import base, creator, tools

# ----- 1. Problem Setup -----
NUM_TRAINS = 25
ACTIONS = ["SERVICE", "STANDBY", "MAINTENANCE"]

# # Example external data (would come from depot systems in real life)
# fitness_certificates = {i: random.choice([True, True, True, False]) for i in range(NUM_TRAINS)}
# job_cards = {i: random.choice(["OPEN", "CLOSED"]) for i in range(NUM_TRAINS)}
# branding_priority = {i: random.randint(0, 1) for i in range(NUM_TRAINS)}

# # Current mileage (in km) for each train
# current_mileage = {i: random.randint(10000, 50000) for i in range(NUM_TRAINS)}

random.seed(42)
np.random.seed(42)


fitness_certificates = {0: True, 1: True, 2: True, 3: False, 4: True, 5: False, 6: True, 7: True, 8: True, 9: True, 10: True, 11: False, 12: True, 13: True, 14: True, 15: False, 16: True, 17: True, 18: True, 19: True, 20: False, 21: True, 22: True, 23: False, 24: False}
job_cards = {0: 'OPEN', 1: 'OPEN', 2: 'OPEN', 3: 'CLOSED', 4: 'CLOSED', 5: 'CLOSED', 6: 'OPEN', 7: 'OPEN', 8: 'CLOSED', 9: 'OPEN', 10: 'OPEN', 11: 'CLOSED', 12: 'CLOSED', 13: 'CLOSED', 14: 'OPEN', 15: 'OPEN', 16: 'OPEN', 17: 'OPEN', 18: 'CLOSED', 19: 'OPEN', 20: 'OPEN', 21: 'CLOSED', 22: 'CLOSED', 23: 'OPEN', 24: 'OPEN'}
branding_priority = {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 0, 12: 0, 13: 0, 14: 1, 15: 1, 16: 0, 17: 1, 18: 0, 19: 1, 20: 1, 21: 1, 22: 0, 23: 1, 24: 0}
current_mileage = {0: 46799, 1: 35244, 2: 47254, 3: 23343, 4: 45072, 5: 34619, 6: 16082, 7: 41051, 8: 38692, 9: 12949, 10: 37534, 11: 38110, 12: 41878, 13: 23661, 14: 27166, 15: 49749, 16: 10278, 17: 27310, 18: 12079, 19: 24676, 20: 42875, 21: 40416, 22: 45784, 23: 49393, 24: 15233}




# Cleaning bay limit per night
MAX_CLEANING_SLOTS = 5

def custom_mutate(individual):
    for i in range(len(individual)):
        if random.random() < 0.1:  # mutation probability
            individual[i] = random.choice(ACTIONS)
    return individual

# ----- 2. Fitness Function -----
def evaluate(individual):
    service_count = sum(1 for action in individual if action == "SERVICE")
    
    penalty = 0

    # Constraint 1: must have at least 15 trains in service
    if service_count < 15:
        penalty += (15 - service_count) * 40

    # Constraint 2: fitness certificate check
    for i, action in enumerate(individual):
        if action == "SERVICE" and not fitness_certificates[i]:
            penalty += 100

    # Constraint 3: job card status
    for i, action in enumerate(individual):
        if action == "SERVICE" and job_cards[i] == "OPEN":
            penalty += 80

    # Constraint 5: branding priority
    for i, action in enumerate(individual):
        if branding_priority[i] == 1 and action != "SERVICE":
            penalty += 30

    # Constraint 6: mileage balancing
    mileage_after = []
    for i, action in enumerate(individual):
        if action == "SERVICE":
            mileage_after.append(current_mileage[i] + 300)
        else:
            mileage_after.append(current_mileage[i])
    penalty += np.var(mileage_after) * 0.01

    # Objective = maximize service, minimize penalty
    return service_count * 100 - penalty,

# ----- 3. GA Setup -----
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("attr_action", lambda: random.choice(ACTIONS))
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_action, n=NUM_TRAINS)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", custom_mutate)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", evaluate)

# ----- 4. Run GA -----
def run_ga():
    pop = toolbox.population(n=150)
    NGEN, CXPB, MUTPB = 80, 0.7, 0.2

    for gen in range(NGEN):
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        # Crossover
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values, child2.fitness.values

        # Mutation
        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Recalculate fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = offspring

    best = tools.selBest(pop, 1)[0]
    return best, best.fitness.values

if __name__ == "__main__":
    best_plan, score = run_ga()
    # print("Best Plan:", best_plan)
    for i in range(len(best_plan)):
        print(i,best_plan[i])
    print('SERVICE',best_plan.count('SERVICE'),'STANDBY',best_plan.count('STANDBY'),'MAINTENANCE',best_plan.count('MAINTENANCE'))
    print("Score:", score)
