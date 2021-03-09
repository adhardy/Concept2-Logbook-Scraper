import json

try:
    fo = open("C2Athletes.json")
    athletes = json.load(fo)
    fo.close
except:
    print("Could not load athletes data file.")
    athletes={}

try:
    fo = open("C2Rankings.json")
    rankings = json.load(fo)
    fo.close
except:
    rankings={"Could not load workouts data file."}

#get basic stats:

#number of workouts
#number of workouts of each event

#number of public athlete profiles
#number of private athlete profiles
#number of logged in only athlete profiles

