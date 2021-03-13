# %%

import json
import pandas as pd
# %%
try:
    #fo = open("output/C2Athletes_cache.json")
    #athletes = json.load(fo)
    df_athletes = pd.read_json("output/C2Athletes_cache.json", orient='index')
    #fo.close
except:
    print("Could not load athletes data file.")
    athletes={}

try:
    # fo = open("output/C2Rankings.json")
    # rankings = json.load(fo)
    # fo.close
except:
    rankings={"Could not load workouts data file."}

try:
    # fo = open("output/C2Extended_cache.json")
    # rankings = json.load(fo)
    # fo.close
except:
    rankings={"Could not load workouts data file."}

# %%
print(df_athletes)
# %%
#get basic stats:

#number of workout
print("Number of workouts: {}".format(len(rankings)))
#number of workouts of each event

#number of public athlete profiles

#number of private athlete profiles
#number of logged in only athlete profiles
