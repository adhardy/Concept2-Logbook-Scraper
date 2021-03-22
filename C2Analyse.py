import json
import pandas as pd
import numpy as np

class df():

    def __init__(self):
        #self.event_map = {"1":"1 minute", "4":"4 minute", "30":"30 minute", "60":"60 minute"}
        self.df_athletes = None
        self.df_extended = None
        self.df_workouts = None

    def load_JSONs(self):
        self.df_athletes = self.df_from_file("output/C2Athletes.json")
        self.df_extended = self.df_from_file("output/C2Extended.json")
        self.df_workouts = self.df_from_file("output/C2Workouts.json")

    def load_csvs(self):
        self.df_athletes = pd.from_csv("output/C2Athletes.json", "profile_id")
        self.df_extended = pd.from_csv("output/C2Extended.json","workout_id")
        self.df_workouts = pd.from_csv("output/C2Workouts.json","workout_id")

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
            try:
                df.to_csv(path)
            except:
                print(f"Could not write csv file: {path}")

    def merge(self, df_workouts, df_athletes, df_extended, how="inner"):
        return pd.merge(left=(pd.merge(left=df_workouts, right=df_athletes, left_on='profile_id', right_on="profile_id", right_index=True, how=how)), 
            right = df_extended, left_on='workout_id', right_on="workout_id", right_index=True, how=how)

class Clean():

    def __init__(self):
        self.df = df()
    

if __name__ == "__main__":

    load_JSON = 1
    load_csv = 0

    clean = Clean()

    if load_JSON == 1:
        clean.df.load_JSONs()
        clean.df.write_csv([clean.df.df_athletes, clean.df.df_extended, clean.df.df_workouts], ["analysis/athletes.csv", "analysis/extended.csv", "analysis/workouts.csv"])

    if load_csv == 1:
        clean.df.loadload_csvs_JSONs()
