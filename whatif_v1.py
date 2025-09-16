import random
import numpy as np
from deap import base, creator, tools
from datetime import date
import pandas as pd
from optimization_algorithm import GA
import time

NUM_TRAINS=25
# Example external data (would come from depot systems in real life)
fitness_certificates = {i: random.choice([True, True, True, False]) for i in range(NUM_TRAINS)}
job_cards = {i: random.choice(["COMPLETED","COMPLETED","INPROGRESS"]) for i in range(NUM_TRAINS)}
branding_priority = {i: random.randint(0, 3) for i in range(NUM_TRAINS)}
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

    def simulate_failure(self,fail_train="MAARUT", fail_time="15:00", shunting_delay=15,criterea=None):
        updated_rows = []
        replacement_log = []
        fail_train=random.choice(random.choice(df['Active_Trains']))
        print(fail_train)
        
        standby_state = None
        active_state = None
        
        for _, row in self.df.iterrows():
            time_slot = row["Time"]
            # active = row["Active_Trains"].copy()
            # standby = row["Standby_Trains"].copy()
            active = active_state.copy() if active_state is not None else row["Active_Trains"].copy()
            standby = standby_state.copy() if standby_state is not None else row["Standby_Trains"].copy()

            if time_slot == fail_time and fail_train in active:
                # remove the failed train
                active.remove(fail_train)
                
                if standby:
                    if criterea == 'milage': 
                        replacement = standby.pop(0)  # take first standby
                        active.append(replacement)
                        replacement_log.append({
                            "Time": time_slot,
                            "Failed": fail_train,
                            "Replacement": replacement,
                            "Delay": f"{shunting_delay} mins"
                        })
                    if criterea == 'branding':
                        t1 = [self.TRAIN_NAMES.index(i) for i in standby]
                        t2 = [branding_priority[i] for i in t1]
                        keyval = self.TRAIN_NAMES[t1[t2.index(max(t2))]]
                        standby.remove(keyval)  # take first standby
                        active.append(keyval)
                        replacement_log.append({
                            "Time": time_slot,
                            "Failed": fail_train,
                            "Replacement": replacement,
                            "Delay": f"{shunting_delay} mins"
                        })


            active_state = active
            standby_state = standby

            updated_rows.append({
                "Time": time_slot,
                "Active_Trains": active,
                "Standby_Trains": standby
            })

        updated_df = pd.DataFrame(updated_rows)
        replacement_df = pd.DataFrame(replacement_log)
        return updated_df, replacement_df
    
    

if __name__=='__main__':
    # Seed with current system time
    # random.seed(time.time())
    # np.random.seed(int(time.time()))
    # Seed with current system time
    random.seed(42)
    np.random.seed(42)
    obj=GA(fitness_certificates=fitness_certificates,job_cards=job_cards,branding_priority=branding_priority,current_mileage=current_mileage)
    obj.GA_setup()
    best_plan, score = obj.run_ga()
    df=obj.time_table(best_plan)
    print(df.to_string(index=False))
    obj2=sim(df=df)
    print('failure')
    a,b=obj2.simulate_failure(criterea='branding')
    print(a.to_string(index=False))
    print(b.to_string(index=False))