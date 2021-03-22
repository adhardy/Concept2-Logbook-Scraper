#%%
import json
import pandas as pd
import numpy as np
import traceback
from datetime import datetime

class df():

    def __init__(self):
        #self.event_map = {"1":"1 minute", "4":"4 minute", "30":"30 minute", "60":"60 minute"}
        self.athletes = None
        self.extended = None
        self.workouts = None

    def load_JSONs(self):
        self.athletes = self.df_from_file("output/C2Athletes.json", "profile_id")
        self.extended = self.df_from_file("output/C2Extended.json", "workout_id")
        self.workouts = self.df_from_file("output/C2Workouts.json", "workout_id")
        self.set_list()

    def load_csvs(self):
        self.dathletes = pd.read_csv("analysis/athletes.csv",sep=",")
        self.extended = pd.read_csv("analysis/extended.csv",sep=",")
        self.workouts = pd.read_csv("analysis/workouts.csv",sep=",")
        self.set_list()

    def set_list(self):
        self.list = [self.athletes, self.extended, self.workouts]

    def df_from_file(self, path, index_name="id"):
        try:
            fa = open(path, "r")
            df = pd.DataFrame.from_dict(json.load(fa)).T
            df.index.set_names(index_name, inplace=True)
            df.replace({"":np.nan, "None":np.nan, None:np.nan}, inplace=True) #all missing values to nan
        except FileNotFoundError:
            print(f"Could not load JSON file: {path}")
            df = None
        return df

    def write_csv(self, dfs, paths):
        for df, path in zip(dfs, paths):
            # try:
            df.to_csv(path)
            # except:
                # print(f"Could not write csv file: {path}")

    def merge_frames(self, how="inner"):
        self.merge = pd.merge(
                    left=(
                        pd.merge(
                            left=self.workouts, 
                            right=self.athletes, 
                            left_on='profile_id', 
                            right_on="profile_id", 
                            right_index=True, 
                            how=how
                            )
                        ), 
                    right = self.extended, 
                    left_on='workout_id', 
                    right_on="workout_id", 
                    right_index=True, 
                    how=how
                    )

    def print_lengths(self):
        print(f"Number of workouts: {len(self.workouts)}")
        print(f"Number of athletes: {len(self.athletes)}")
        print(f"Number of extended workout data: {len(self.extended)}")
        print(f"Number of merged data: {len(self.merge)}")

class Clean():

    def __init__(self, verbose = 0):
        self.df = df()
        self.verbose = verbose
        self.ft_to_cm = 30.48
        self.in_to_cm = 2.54

    def load_JSON(self):
        if self.verbose == 1:
            print("Loading JSON.")
        self.df.load_JSONs()
        self.df.write_csv(self.df.list, ["analysis/athletes.csv", "analysis/extended.csv", "analysis/workouts.csv"])
        if self.verbose == 1:
            print("Loaded.")

    def load_csv():
        self.df.load_csvs()

def convert_to_datetime(date_str):
    dtFormats = ('%B %d, %Y','%B %d, %Y %H:%M:%S','%d-%m-%Y %H:%M:%S')
    date_value = None
    if isinstance(date_str, datetime):
        #return if already a datetime
        return date_str
    if isinstance(date_str, str): 
        date_str = date_str.strip()
        for dtFormat in dtFormats:
            try:
                date_value = datetime.strptime(date_str, dtFormat)
            except ValueError:
                pass
            else:
                return date_value
        if date_value == None:
            raise ValueError(f"No mathing datetime format found for '{date_str}'")