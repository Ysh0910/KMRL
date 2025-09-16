import random
import numpy as np
from deap import base, creator, tools
from datetime import date
import pandas as pd
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
class GA():
    def __init__(self,fitness_certificates,job_cards,branding_priority,current_mileage):
        self.fitness_certificates = fitness_certificates
        self.job_cards = job_cards
        self.branding_priority = branding_priority
        self.current_mileage = current_mileage
        self.MAX_CLEANING_SLOTS = 5
        self.NUM_TRAINS = 25
        self.ACTIONS = ["SERVICE", "STANDBY", "MAINTENANCE"]
        self.TRAIN_NAMES = [
            "KRISHNA",
            "TAPTI",
            "NILA",
            "SARAYU",
            "ARUTH",
            "VAIGAI",
            "JHANAVI",
            "DHWANIL",
            "BHAVANI",
            "PADMA",
            "MANDAKINI",
            "YAMUNA",
            "PERIYAR",
            "KABANI",
            "VAAYU",
            "KAVERI",
            "SHIRIYA",
            "PAMPA",
            "NARMADA",
            "MAHE",
            "MAARUT",
            "SABARMATHI",
            "GODHAVARI",
            "GANGA",
            "PAVAN"
        ]
        random.seed(42)
        np.random.seed(42)

    def custom_mutate(self,individual):
        for i in range(len(individual)):
            if random.random() < 0.1:  # mutation probability
                individual[i] = random.choice(self.ACTIONS)
        return individual

    # ----- 2. Fitness Function -----
    def evaluate(self,individual):
        service_count = sum(1 for action in individual if action == "SERVICE")
        
        penalty = 0
        reward = 0
        # Constraint 1: must have at least 15 trains in service
        if service_count > 8:
            penalty += (8 - service_count) * 100

        # Constraint 2: fitness certificate check
        for i, action in enumerate(individual):
            if action == "SERVICE" and self.fitness_certificates[i] == False:
                penalty += 100

        # Constraint 3: job card status
        for i, action in enumerate(individual):
            if action == "SERVICE" and self.job_cards[i] == "INPROGRESS":
                penalty += 100

        # Constraint 5: branding priority (inverse scaling)
        for i, action in enumerate(individual):
            if action != "SERVICE":
                # Higher branding_priority → smaller penalty
                penalty += (6 - self.branding_priority[i]) * 50  


        # Constraint 6: mileage balancing
        mileage_after = []
        for i, action in enumerate(individual):
            if action == "SERVICE":
                mileage_after.append(self.current_mileage[i] + 540)
            else:
                mileage_after.append(self.current_mileage[i])
        penalty += np.var(mileage_after) * 0.01

        for i, action in enumerate(individual):
            if action == "MAINTENANCE" and self.fitness_certificates[i] == False and self.job_cards[i] == "INPROGRESS":
                reward += 100
            
        rf=0
        for i, action in enumerate(individual):
            if action == "MAINTENANCE":
                rf+=1
        if rf>self.MAX_CLEANING_SLOTS:
            penalty+=(rf-self.MAX_CLEANING_SLOTS)*100

        # Objective = maximize service, minimize penalty
        return reward+service_count * 100 - penalty,

    # ----- 3. GA Setup -----
    def GA_setup(self,):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_action", lambda: random.choice(self.ACTIONS))
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, self.toolbox.attr_action, n=self.NUM_TRAINS)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self.custom_mutate)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("evaluate", self.evaluate)

# ----- 4. Run GA -----
    def run_ga(self):
        pop = self.toolbox.population(n=150)
        NGEN, CXPB, MUTPB = 80, 0.7, 0.2

        for gen in range(NGEN):
            offspring = self.toolbox.select(pop, len(pop))
            offspring = list(map(self.toolbox.clone, offspring))

            # Crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values, child2.fitness.values

            # Mutation
            for mutant in offspring:
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Recalculate fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            pop[:] = offspring

        best = tools.selBest(pop, 1)[0]
        return best, best.fitness.values

    def time_table(self,best_plan:list):
        l=[]
        for i in range(len(best_plan)):
            if best_plan[i] == 'SERVICE' or  best_plan[i] == 'STANDBY':
                l.append([i,best_plan[i],fitness_certificates[i],job_cards[i],branding_priority[i],current_mileage[i]])            
        
        
        standby_pool = sorted([t for t in l if t[1]=="STANDBY" and t[2]==True and t[3]=='COMPLETED'], key=lambda x: x[5])
        service_pool = sorted([t for t in l if t[1]=="SERVICE" and t[2]==True and t[3]=='COMPLETED'], key=lambda x: x[5])

        active = service_pool[:8]
        standby = standby_pool + service_pool[8:]

        day=date.today()
        if day.weekday()==6:
            slots = pd.date_range("06:00", "22:30", freq="60min").strftime("%H:%M").tolist()
        else:
            slots = pd.date_range("08:00", "22:30", freq="60min").strftime("%H:%M").tolist()
        timetable = []

        for slot in slots:
            timetable.append((slot, [self.TRAIN_NAMES[t[0]] for t in active],[self.TRAIN_NAMES[t[0]] for t in standby]))  # record active trains
            # Increase mileage by ~27 km per hour (Kochi Metro line length)
            active = [(tid, "SERVICE", fit, job, brand, m+45) for tid,_,fit,job,brand,m in active]
            
            # Check if any train needs rotation (>500 km in the day or mileage > 48000)
            for idx, (tid,_,fit,job,brand,m) in enumerate(active):
                if (m - [x for x in l if x[0]==tid][0][5]) > 500 or m > 48000:
                    for idx, (tid,_,fit,job,brand,m) in enumerate(standby):
                        if (m - [x for x in l if x[0]==tid][0][5]) > 500 or m > 48000:
                            replacement = standby.pop(0)
                            standby.append((tid,"STANDBY",fit,job,brand,m))
                            active[idx] = (replacement[0],"SERVICE",replacement[2],replacement[3],replacement[4],replacement[5])

        for idx, (tid,_,fit,job,brand,m) in enumerate(active): 
            print(self.TRAIN_NAMES[idx],m)
        for idx, (tid,_,fit,job,brand,m) in enumerate(standby): 
            print(self.TRAIN_NAMES[idx],m)
        # ----- Output -----
        df = pd.DataFrame(timetable, columns=["Time", "Active_Trains","Standby_Trains"])
        return df

class TrainScheduleAPIView(APIView):
     """Django APIView that accepts JSON input with fitness_certificates, 
        job_cards, branding_priority, and current_mileage."""
     def post(self, request, *args, **kwargs):
        # Extract input JSON
        try:
            fitness_certificates = request.data["fitness_certificates"]
            job_cards = request.data["job_cards"]
            branding_priority = request.data["branding_priority"]
            current_mileage = request.data["current_mileage"]
        except KeyError as e:
            return Response(
                {"error": f"Missing field {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fitness_certificates = {int(k): v for k, v in fitness_certificates.items()}
        job_cards = {int(k): v for k, v in job_cards.items()}
        branding_priority = {int(k): v for k, v in branding_priority.items()}
        current_mileage = {int(k): v for k, v in current_mileage.items()}

        obj=GA(fitness_certificates=fitness_certificates,job_cards=job_cards,branding_priority=branding_priority,current_mileage=current_mileage)
        obj.GA_setup()
        best_plan, score = obj.run_ga()
        df=obj.time_table(best_plan) 

        return Response({
            "best_schedule": df,
        }, status=status.HTTP_200_OK)

if __name__=='__main__':
    fitness_certificates = {0: True, 1: True, 2: True, 3: True, 4: True, 5: False, 6: True, 7: True, 8: False, 9: True, 10: True, 11: True, 12: False, 13: True, 14: True, 15: True, 16: False, 17: True, 18: False, 19: True, 20: True, 21: True, 22: True, 23: True, 24: False}
    job_cards = {0: 'COMPLETED', 1: 'INPROGRESS', 2: 'COMPLETED', 3: 'INPROGRESS', 4: 'COMPLETED', 5: 'COMPLETED', 6: 'COMPLETED', 7: 'COMPLETED', 8: 'COMPLETED', 9: 'COMPLETED', 10: 'INPROGRESS', 11: 'COMPLETED', 12: 'INPROGRESS', 13: 'COMPLETED', 14: 'INPROGRESS', 15: 'COMPLETED', 16: 'COMPLETED', 17: 'COMPLETED', 18: 'COMPLETED', 19: 'COMPLETED', 20: 'COMPLETED', 21: 'COMPLETED', 22: 'INPROGRESS', 23: 'INPROGRESS', 24: 'COMPLETED'}
    branding_priority = {0: 2, 1: 3, 2: 3, 3: 3, 4: 1, 5: 3, 6: 3, 7: 0, 8: 3, 9: 3, 10: 0, 11: 3, 12: 0, 13: 1, 14: 2, 15: 1, 16: 1, 17: 0, 18: 1, 19: 0, 20: 3, 21: 2, 22: 0, 23: 2, 24: 1}
    current_mileage = {0: 11794, 1: 14108, 2: 34759, 3: 43713, 4: 24540, 5: 46170, 6: 20618, 7: 44674, 8: 38474, 9: 25519, 10: 14670, 11: 43083, 12: 46581, 13: 16176, 14: 14787, 15: 40948, 16: 12268, 17: 40026, 18: 42357, 19: 20693, 20: 25369, 21: 32165, 22: 43456, 23: 43912, 24: 44504}
    obj=GA(fitness_certificates=fitness_certificates,job_cards=job_cards,branding_priority=branding_priority,current_mileage=current_mileage)
    obj.GA_setup()
    best_plan, score = obj.run_ga()
    # df=obj.time_table(best_plan)
    print(best_plan)
    print('SERVICE',best_plan.count('SERVICE'),'STANDBY',best_plan.count('STANDBY'),'MAINTENANCE',best_plan.count('MAINTENANCE'))
    print(score)
    # print(df.to_string(index=False))
    
    
    