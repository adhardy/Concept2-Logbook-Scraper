import json
import pandas as pd
import numpy as np

class df():

    def __init__(self):
        self.event_map = {"1":"1 minute", "4":"4 minute", "30":"30 minute", "60":"60 minute"}

    def load_from_file(path):
        try:
            fa = open(path, "r")
            df = pd.DataFrame.from_dict(json.load(fa)).T
            df.replace({"":np.nan, "None":np.nan, "None":None}, inplace=True) #all missing values to nan
        except:
            print("Could not load workouts data file.")
            df = None
            
        return df

    def merge(df_workouts, df_athletes, df_extended, how="inner"):
        return pd.merge(left=(pd.merge(left=df_workouts, right=df_athletes, left_on='profile_id', right_on="profile_id", right_index=True, how=how)), 
            right = df_extended, left_on='workout_id', right_on="workout_id", right_index=True, how=how)