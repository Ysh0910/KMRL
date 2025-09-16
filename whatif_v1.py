import random
import numpy as np
from deap import base, creator, tools
from datetime import date
import pandas as pd
import time
import json
from optimization_algorithm import GA
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

NUM_TRAINS=25
# Example external data (would come from depot systems in real life)
fitness_certificates = {i: random.choice([True, True, True, False]) for i in range(NUM_TRAINS)}
job_cards = {i: random.choice(["COMPLETED","COMPLETED","INPROGRESS"]) for i in range(NUM_TRAINS)}
branding_priority = {i: random.randint(0, 5) for i in range(NUM_TRAINS)}
current_mileage = {i: random.randint(10000, 50000) for i in range(NUM_TRAINS)}
class sim():
    def __init__(self,df):
        self.df=df       
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

    def simulate_failure(self, failures, criterea="milage", brandingpriority=None):
        """
        failures: list of dicts [{"train": "PADMA", "time": "15:00"}, ...]
        criterea: 'milage' or 'branding'
        """
        updated_rows = []
        replacement_log = []

        # Keep running state of active & standby (carry forward changes)
        active = None
        standby = None

        for _, row in self.df.iterrows():
            time_slot = row["Time"]

            # At the very first row, initialize with current schedule
            if active is None:
                active = row["Active_Trains"].copy()
                standby = row["Standby_Trains"].copy()
            else:
                # Carry forward previous state
                active = active.copy()
                standby = standby.copy()

            # Check all failures scheduled at this time slot
            for failure in failures:
                fail_train = failure["train"]
                fail_time = failure["time"]

                if time_slot == fail_time and fail_train in active:
                    # remove the failed train
                    active.remove(fail_train)

                    if standby:
                        if criterea == "milage":
                            replacement = standby.pop(0)

                        elif criterea == "branding" and brandingpriority:
                            t1 = [self.TRAIN_NAMES.index(i) for i in standby]
                            t2 = [brandingpriority[i] for i in t1]
                            replacement = self.TRAIN_NAMES[t1[t2.index(max(t2))]]
                            standby.remove(replacement)

                        else:
                            replacement = standby.pop(0)

                        active.append(replacement)
                        replacement_log.append({
                            "Time": time_slot,
                            "Failed": fail_train,
                            "Replacement": replacement
                        })

            # Save updated row for this time slot
            updated_rows.append({
                "Time": time_slot,
                "Active_Trains": active.copy(),
                "Standby_Trains": standby.copy()
            })

        updated_df = pd.DataFrame(updated_rows)
        self.df = updated_df
        replacement_df = pd.DataFrame(replacement_log)

        return updated_df, replacement_df


class SimulationAPIView(APIView):
     """Django APIView that accepts JSON input with action """
     def post(self, request, *args, **kwargs):
        try:

            # fitness_certificates = request.data["fitness_certificates"]
            # job_cards = request.data["job_cards"]
            # branding_priority = request.data["branding_priority"]
            # current_mileage = request.data["current_mileage"]
            random.seed(time.time())
            np.random.seed(int(time.time()))
            fitness_certificates = {i: random.choice([True, True, True, False]) for i in range(NUM_TRAINS)}
            job_cards = {i: random.choice(["COMPLETED","COMPLETED","INPROGRESS"]) for i in range(NUM_TRAINS)}
            branding_priority = {i: random.randint(0, 3) for i in range(NUM_TRAINS)}
            current_mileage = {i: random.randint(10000, 50000) for i in range(NUM_TRAINS)}
            obj=GA(fitness_certificates=fitness_certificates,job_cards=job_cards,branding_priority=branding_priority,current_mileage=current_mileage)
            obj.GA_setup()
            best_plan, score = obj.run_ga()
            df=obj.time_table(best_plan)
            action = request.data.get("action")
            failures = request.data.get("failures", [])
            criteria = request.data.get("criteria", None)
            obj2=sim(df=df)
            a,b = obj2.simulate_failure(failures=failures,criteria=criteria,brandingpriority=branding_priority)
            return Response({
                    "time_table": a,
                    "report":b
                }, status=status.HTTP_200_OK)    

        except KeyError as e:
            return Response(
                {"error": f"Missing field {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )    
    

if __name__=='__main__':
    # Seed with current system time
    random.seed(time.time())
    np.random.seed(int(time.time()))
    # Seed with current system time
    obj=GA(fitness_certificates=fitness_certificates,job_cards=job_cards,branding_priority=branding_priority,current_mileage=current_mileage)
    obj.GA_setup()
    best_plan, score = obj.run_ga()
    print('SERVICE',best_plan.count('SERVICE'),'STANDBY',best_plan.count('STANDBY'),'MAINTENANCE',best_plan.count('MAINTENANCE'))
    for i in range(len(best_plan)):
        print(obj.TRAIN_NAMES[i],best_plan[i],fitness_certificates[i],job_cards[i],current_mileage[i],branding_priority[i])
    df=obj.time_table(best_plan)
    print(df.to_string(index=False))
    obj2=sim(df=df)
    print('failure')
    failures = [
    {"train": "PADMA", "time": "14:00"},
    {"train": "YAMUNA", "time": "15:00"},
    ]
    a,b=obj2.simulate_failure(failures=failures,criterea='branding',brandingpriority=branding_priority)
    print(a.to_string(index=False))
    print(b.to_string(index=False))