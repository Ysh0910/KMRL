import random
import numpy as np
from deap import base, creator, tools
from datetime import date, datetime
import pandas as pd
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
import requests
import json

# --- Data Processing Functions ---

def process_fitness_certificates(data):
    """Processes fitness certificate data to determine the status of each train."""
    processed_data = {}
    today = datetime.now().date()

    for cert in data:
        train_id = cert.get("train_id")
        if train_id is None:
            continue

        validity_date_str = cert.get("validity")
        is_valid = False
        if validity_date_str:
            try:
                validity_date = datetime.strptime(validity_date_str, "%Y-%m-%d").date()
                if validity_date >= today:
                    braking_ok = cert.get("braking", False)
                    signaling_ok = cert.get("signaling", False)
                    structural_ok = cert.get("structural", False)
                    if all([braking_ok, signaling_ok, structural_ok]):
                        is_valid = True
            except (ValueError, TypeError):
                pass  # is_valid remains False
        
        processed_data[int(train_id)] = is_valid
        
    return processed_data

def process_job_card_status(data):
    """Processes job card data to get the status for each train."""
    processed_data = {}
    for job in data:
        train_id = job.get("train_id")
        status = job.get("status")
        if train_id is not None and status:
            processed_data[int(train_id)] = status
    return processed_data

def process_branding_priorities(data):
    """Processes branding priorities to assign a score based on revenue and impressions."""
    processed_data = {}
    today = datetime.now().date()

    for contract in data:
        train_id = contract.get("trainid")
        if train_id is None:
            continue

        score = 0
        start_date_str = contract.get("start_date")
        end_date_str = contract.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                if start_date <= today <= end_date:
                    revenue = float(contract.get("perday_revenue", 0))
                    impression = int(contract.get("impression", 0))
                    
                    if revenue > 5000 or impression > 10000:
                        score = 5
                    elif revenue > 3000 or impression > 7000:
                        score = 4
                    elif revenue > 2000 or impression > 5000:
                        score = 3
                    elif revenue > 1000 or impression > 3000:
                        score = 2
                    else:
                        score = 1
            except (ValueError, TypeError):
                pass # score remains 0
        
        processed_data[int(train_id)] = score
                
    return processed_data

def process_mileage(data):
    """Processes mileage data, converting it to integers."""
    processed_data = {}
    for item in data:
        train_id = item.get("train_id")
        mileage_float = item.get("mileage")
        if train_id is not None and mileage_float is not None:
            processed_data[int(train_id)] = int(mileage_float)
    return processed_data

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
            "KRISHNA", "TAPTI", "NILA", "SARAYU", "ARUTH", "VAIGAI", "JHANAVI",
            "DHWANIL", "BHAVANI", "PADMA", "MANDAKINI", "YAMUNA", "PERIYAR",
            "KABANI", "VAAYU", "KAVERI", "SHIRIYA", "PAMPA", "NARMADA", "MAHE",
            "MAARUT", "SABARMATHI", "GODHAVARI", "GANGA", "PAVAN"
        ]
        random.seed(42)
        np.random.seed(42)

    def custom_mutate(self,individual):
        for i in range(len(individual)):
            if random.random() < 0.1:  # mutation probability
                individual[i] = random.choice(self.ACTIONS)
        return individual

    def evaluate(self,individual):
        service_count = sum(1 for action in individual if action == "SERVICE")
        
        penalty = 0
        reward = 0
        if service_count > 8:
            penalty += (8 - service_count) * 100

        for i, action in enumerate(individual):
            if action == "SERVICE" and not self.fitness_certificates.get(i, True):
                penalty += 100

        for i, action in enumerate(individual):
            if action == "SERVICE" and self.job_cards.get(i) == "INPROGRESS":
                penalty += 100

        for i, action in enumerate(individual):
            if action != "SERVICE":
                penalty += (4 - self.branding_priority.get(i, 0)) * 50  

        mileage_after = []
        for i, action in enumerate(individual):
            current_mileage = self.current_mileage.get(i, 0)
            if action == "SERVICE":
                mileage_after.append(current_mileage + 300)
            else:
                mileage_after.append(current_mileage)
        penalty += np.var(mileage_after) * 0.01

        for i, action in enumerate(individual):
            if action == "MAINTENANCE" and not self.fitness_certificates.get(i, True) and self.job_cards.get(i) == "INPROGRESS":
                reward += 100    

        return reward + service_count * 100 - penalty,

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

    def run_ga(self):
        pop = self.toolbox.population(n=150)
        NGEN, CXPB, MUTPB = 80, 0.7, 0.2

        for gen in range(NGEN):
            offspring = self.toolbox.select(pop, len(pop))
            offspring = list(map(self.toolbox.clone, offspring))

            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values, child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

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
                l.append([i,best_plan[i],self.fitness_certificates.get(i),self.job_cards.get(i),self.branding_priority.get(i,0),self.current_mileage.get(i,0)])            
        
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
            timetable.append((slot, [self.TRAIN_NAMES[t[0]] for t in active],[self.TRAIN_NAMES[t[0]] for t in standby]))
            active = [(tid, "SERVICE", fit, job, brand, m+45) for tid,_,fit,job,brand,m in active]
            
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
        df = pd.DataFrame(timetable, columns=["Time", "Active_Trains","Standby_Trains"])
        return df

class TrainScheduleAPIView(APIView):
     """Django APIView that accepts JSON input with fitness_certificates, 
        job_cards, branding_priority, and current_mileage."""
     def post(self, request, *args, **kwargs):
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
            "best_schedule": df.to_dict('records'),
        }, status=status.HTTP_200_OK)

if __name__=='__main__':
    DATA_URL = "http://localhost:8000/postmodeldata"

    def fetch_and_process_data(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            raw_data = response.json()

            fitness_data = raw_data.get("fitness_certificates", [])
            job_card_data = raw_data.get("job_card_status", [])
            branding_data = raw_data.get("branding_priorities", [])
            mileage_data = raw_data.get("mileage", [])

            fitness_certificates = process_fitness_certificates(fitness_data)
            job_cards = process_job_card_status(job_card_data)
            branding_priority = process_branding_priorities(branding_data)
            current_mileage = process_mileage(mileage_data)

            return fitness_certificates, job_cards, branding_priority, current_mileage

        except requests.exceptions.RequestException as e:
            print(f"Error fetching or processing data: {e}")
            return {}, {}, {}, {}
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from response.")
            return {}, {}, {}, {}

    fitness_certificates, job_cards, branding_priority, current_mileage = fetch_and_process_data(DATA_URL)

    if fitness_certificates and job_cards and branding_priority and current_mileage:
        obj=GA(fitness_certificates=fitness_certificates,job_cards=job_cards,branding_priority=branding_priority,current_mileage=current_mileage)
        obj.GA_setup()
        best_plan, score = obj.run_ga()
        df=obj.time_table(best_plan)
        print("GA run successful. Timetable generated.")
        # print(df.to_string(index=False))
    else:
        print("Could not run GA due to missing data.")