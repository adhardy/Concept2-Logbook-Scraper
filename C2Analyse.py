import json
import pandas as pd
import numpy as np
import traceback

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
        self.set_list()

    def load_csvs(self):
        self.df_athletes = pd.from_csv("output/C2Athletes.json", "profile_id")
        self.df_extended = pd.from_csv("output/C2Extended.json","workout_id")
        self.df_workouts = pd.from_csv("output/C2Workouts.json","workout_id")
        self.set_list()

    def set_list(self):
        self.list = [self.df_athletes, self.df_extended, self.df_workouts]

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

    def merge(self, how="inner"):
        return pd.merge(
                    left=(
                        pd.merge(
                            left=self.df_workouts, 
                            right=self.df_athletes, 
                            left_on='profile_id', 
                            right_on="profile_id", 
                            right_index=True, 
                            how=how
                            )
                        ), 
                    right = self.df_extended, 
                    left_on='workout_id', 
                    right_on="workout_id", 
                    right_index=True, 
                    how=how
                    )

    def print_lengths(self):
        print(f"Number of workouts: {len(self.df_workouts)}")
        print(f"Number of athletes: {len(self.df_athletes)}")
        print(f"Number of extended workout data: {len(self.df_extended)}")

class Clean():

    def __init__(self, load_JSON = 1, load_csv = 0):
        self.df = df()

        if load_JSON == 1:
            self.df.load_JSONs()
            self.df.write_csv(self.df.list, ["analysis/athletes.csv", "analysis/extended.csv", "analysis/workouts.csv"])

        if load_csv == 1:
            self.df.load_csvs_JSONs()

        self.df.print_lengths()

if __name__ == "__main__":

    clean = Clean()


