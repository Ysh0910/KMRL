import random
import numpy as np
from deap import base, creator, tools

# ----- 1. Problem Setup -----
NUM_TRAINS = 25
ACTIONS = ["SERVICE", "STANDBY", "MAINTENANCE"]

# Example external data (would come from depot systems in real life)
fitness_certificates = {i: random.choice([True, True, True, False]) for i in range(NUM_TRAINS)}
job_cards = {i: random.choice(["COMPLETED", "INPROGRESS"]) for i in range(NUM_TRAINS)}
branding_priority = {i: random.randint(0, 3) for i in range(NUM_TRAINS)}

# Current mileage (in km) for each train
current_mileage = {i: random.randint(10000, 50000) for i in range(NUM_TRAINS)}

random.seed(42)
np.random.seed(42)


# fitness_certificates = {0: True, 1: True, 2: True, 3: True, 4: True, 5: False, 6: True, 7: True, 8: False, 9: True, 10: True, 11: True, 12: False, 13: True, 14: True, 15: True, 16: False, 17: True, 18: False, 19: True, 20: True, 21: True, 22: True, 23: True, 24: False}
# job_cards = {0: 'COMPLETED', 1: 'INPROGRESS', 2: 'COMPLETED', 3: 'INPROGRESS', 4: 'COMPLETED', 5: 'COMPLETED', 6: 'COMPLETED', 7: 'COMPLETED', 8: 'COMPLETED', 9: 'COMPLETED', 10: 'INPROGRESS', 11: 'COMPLETED', 12: 'INPROGRESS', 13: 'COMPLETED', 14: 'INPROGRESS', 15: 'COMPLETED', 16: 'COMPLETED', 17: 'COMPLETED', 18: 'COMPLETED', 19: 'COMPLETED', 20: 'COMPLETED', 21: 'COMPLETED', 22: 'INPROGRESS', 23: 'INPROGRESS', 24: 'COMPLETED'}
# branding_priority = {0: 2, 1: 3, 2: 3, 3: 3, 4: 1, 5: 3, 6: 3, 7: 0, 8: 3, 9: 3, 10: 0, 11: 3, 12: 0, 13: 1, 14: 2, 15: 1, 16: 1, 17: 0, 18: 1, 19: 0, 20: 3, 21: 2, 22: 0, 23: 2, 24: 1}
# current_mileage = {0: 11794, 1: 14108, 2: 34759, 3: 43713, 4: 24540, 5: 46170, 6: 20618, 7: 44674, 8: 38474, 9: 25519, 10: 14670, 11: 43083, 12: 46581, 13: 16176, 14: 14787, 15: 40948, 16: 12268, 17: 40026, 18: 42357, 19: 20693, 20: 25369, 21: 32165, 22: 43456, 23: 43912, 24: 44504}


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
    reward = 0
    # Constraint 1: must have at least 15 trains in service
    if service_count > 8:
        penalty += (8 - service_count) * 100

    # Constraint 2: fitness certificate check
    for i, action in enumerate(individual):
        if action == "SERVICE" and fitness_certificates[i] == False:
            penalty += 100

    # Constraint 3: job card status
    for i, action in enumerate(individual):
        if action == "SERVICE" and job_cards[i] == "INPROGRESS":
            penalty += 100

    # Constraint 5: branding priority (inverse scaling)
    for i, action in enumerate(individual):
        if action != "SERVICE":
            # Higher branding_priority → smaller penalty
            penalty += (4 - branding_priority[i]) * 50  


    # Constraint 6: mileage balancing
    mileage_after = []
    for i, action in enumerate(individual):
        if action == "SERVICE":
            mileage_after.append(current_mileage[i] + 300)
        else:
            mileage_after.append(current_mileage[i])
    penalty += np.var(mileage_after) * 0.01

    for i, action in enumerate(individual):
        if action == "MAINTENANCE" and fitness_certificates[i] == False and job_cards[i] == "INPROGRESS":
            reward += 100    

    # Objective = maximize service, minimize penalty
    return reward+service_count * 100 - penalty,

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
    a,b,c,d,e=0,0,0,0,0
    for i in range(len(best_plan)):
        print(i,best_plan[i],fitness_certificates[i],job_cards[i],branding_priority[i],current_mileage[i])
        if fitness_certificates[i]==True and job_cards[i]== 'COMPLETED':
            a+=1
        if best_plan[i]=='SERVICE' and fitness_certificates[i]==True and job_cards[i]== 'COMPLETED':
            b+=1
        if best_plan[i]=='STANDBY' and fitness_certificates[i]==True and job_cards[i]== 'COMPLETED':
            e+=1    
        if fitness_certificates[i]==False and job_cards[i]== 'INPROGRESS':
            c+=1
        if best_plan[i]=='MAINTENANCE' and fitness_certificates[i]==False and job_cards[i]== 'INPROGRESS':
            d+=1
    print(a,b)
    print(e)
    print(c,d)
    print('SERVICE',best_plan.count('SERVICE'),'STANDBY',best_plan.count('STANDBY'),'MAINTENANCE',best_plan.count('MAINTENANCE'))
    print(score)

