import json
import pandas as pd

def load_C2scrape_data(path):
    try:
        fa = open(path, "r")
        df = pd.DataFrame.from_dict(json.load(fa)).T
    except:
        print("Could not load workouts data file.")
        df = None
    return df
