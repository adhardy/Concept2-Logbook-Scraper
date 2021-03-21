import C2Scrape
from multi_webbing import multi_webbing as mw
import string
import json
from lxml import etree, html #reading html 
import queue #multithreading
import threading
from datetime import datetime, date
from time import strftime,gmtime
import time #sleep
import sys
import requests
#TODO: os.path.join(),aws rds

config = {}
config = C2Scrape.load_config("C2config.json")

#load config into easy to use vars
get_extended_workout_data = config["get_extended_workout_data"]
get_profile_data = config["get_profile_data"]
url_profile_base = config["url_profile_base"]

#initialise data structures and output files
data = C2Scrape.Data(config)
if config["use_cache"] == True:
    cache = C2Scrape.Cache(config)
else:
    cache=None

# initialize threads
threads = mw.MultiWebbing(config["threads"])

#use same session as threads, log in to the website
s = threads.session
if config["C2_login"]:
    #TODO move loading of username password to environment vars rather than config file
    C2Scrape.C2_login(s, config["url_login"], config["C2_username"], config["C2_password"], "https://log.concept2.com/log")

# start threads
threads.start()

#generate urls to visit
ranking_tables = C2Scrape.generate_C2Ranking_urls(config["machine_parameters"], config["url_parameters"]["url_years"], config["url_parameters"]["url_base"])
num_ranking_tables = len(ranking_tables)

#check for override of maximum urls
if config["max_ranking_tables"] != "":
    num_ranking_tables = int(config["max_ranking_tables"])

ranking_table_count = 0 #counts the number of ranking table objects processed
queue_added = 0 #counts the total number of objects added to the queue

#main loop for master process over each ranking table
queue_added = 0
for ranking_table in ranking_tables[0:num_ranking_tables]: 
    ranking_table_count += 1
    ranking_table.scrape(ranking_table_count, threads, queue_added, num_ranking_tables, data, cache)

print("Finished scraping ranking tables, waiting for profile threads to finish...")

# wait for queue to be empty, then join the threads
while not threads.job_queue.empty():
    time.sleep(1)
    print(f"Queue size: {str(threads.job_queue.qsize())}/{queue_added}")
    threads.lock.acquire()
    if C2Scrape.check_write_buffer(timestamp_last_write, write_buffer):
        C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
        if config["use_cache"] == True:
            C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])
        timestamp_last_write = datetime.now().timestamp()
    threads.lock.release()

#final write
C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
if config["use_cache"] == True:
    C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])

if threads.job_queue.empty():
    #join threads
    threads.finish()

print("Finished!")
