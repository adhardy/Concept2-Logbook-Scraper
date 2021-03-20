import json
import pandas as pd

class C2Analysis():

    def __init__(self)
        self.event_map = {"1":"1 minute", "4":"4 minute", "30":"30 minute", "60":"60 minute"}

    def load_C2scrape_data(path):
        try:
            fa = open(path, "r")
            df = pd.DataFrame.from_dict(json.load(fa)).T
        except:
            print("Could not load workouts data file.")
            df = None
        return df

