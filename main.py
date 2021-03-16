import C2Scrape
import multi_webbing as mw
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
try:
    fo = open("C2config.json")
    config = json.load(fo)
    fo.close
except:
    print("Could not open config file. Quitting")
    quit()

#load config into easy to use vars
url_login_success = "https://log.concept2.com/log"
write_buffer = config["write_buffer"] #write every X ranking pages
get_extended_workout_data = config["get_extended_workout_data"]
get_profile_data = config["get_profile_data"]
workouts_file = config["workouts_file"]
athletes_file = config["athletes_file"]
extended_file = config["extended_file"]
athletes_cache_file = config["athletes_cache_file"]
extended_cache_file = config["extended_cache_file"]
url_profile_base = config["url_profile_base"]
url_login = config["url_login"]
#TODO move loading of username password to environment vars rather than config file
C2_login = config["C2_login"]
C2_username = config["C2_username"]
C2_password = config["C2_password"]
athletes = {}
workouts = {}
ext_workouts = {}

#create session for login
s = requests.session()
if C2_login:
    response = C2Scrape.C2_login(s, url_login, C2_username, C2_password)
    if response.url != url_login_success:
        sys.exit("Unable to login to the logbook, quitting.")
    else:
        print("Login")
else:
    print("Loggin set to false, not loggin in")

# initializing threads
THREADS = config["threads"]
threads = []
profile_queue = queue.Queue()
lock = threading.Lock()
for i in range(THREADS):
    threads.append(mw.ProfileThread(str(i), profile_queue))

# start the threads
for i in range(THREADS): #TODO update all these loops with len(threads)
    threads[i].start()

#backup previous output
for file in [workouts_file, athletes_file, extended_file, athletes_cache_file, extended_cache_file]:
    C2Scrape.backup_file(file)

#load cache files
if config["use_cache"] == True:
    athletes_cache = C2Scrape.load_cache(athletes_cache_file)
    ext_workouts_cache = C2Scrape.load_cache(extended_cache_file)
else:
    athletes_cache = {}
    ext_workouts_cache = {}

#generate urls to visit
ranking_tables = C2Scrape.generate_C2Ranking_urls(config["machine_parameters"], config["url_parameters"]["url_years"], config["url_parameters"]["url_base"])
num_ranking_tables = len(ranking_tables)

#check for override of maximum urls
if config["max_ranking_tables"] != "":
    num_ranking_tables = int(config["max_ranking_tables"])-1

#initialize output files
C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
if config["use_cache"] == "True":
    C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athlete_profiles_cache, ext_workouts_cache])
timestamp_last_write = datetime.now().timestamp()

ranking_table_count = 0 #counts the number of ranking table objects processed
queue_added = 0 #counts the total number of objects added to the queue

#main loop for master process over each ranking table
for ranking_table in ranking_tables[0:num_ranking_tables+1]: 
    ranking_table_count += 1
    r = C2Scrape.get_url(s, ranking_table.url_string)

    #find the number of pages for this ranking table
    if r != None:
        tree = html.fromstring(r.text)
        pagination_block = tree.xpath('//div[@class="pagination-block"]')
        if pagination_block != []:
            page_a_tag = pagination_block[0].xpath('ul/li/a')
            #find the second to last one
            pages = int(page_a_tag[-2].text)
        else:
            #no pagination block, only one page
            pages = 1
    
    for page in range(1,pages+1):
        #master process sub-loop over each page
        url_string = ranking_table.url_string + "&page=" + str(page)

        print(C2Scrape.get_str_ranking_table_progress(profile_queue.qsize(), queue_added, ranking_table_count,num_ranking_tables,page,pages) + "Getting ranking page: " + url_string)
        if page > 1:
            #don't get the first page again (if page is ommitted, page 1 is loaded)
            workouts_page=[]
            r = C2Scrape.get_url(s, url_string)
        #master process checks each row, adds URLs to queue for threads to visit
        if r != None:
            tree = html.fromstring(r.text)
            table_tree = tree.xpath('//html/body/div[2]/div/main/section[@class="content"]/table')
            
            #get column headings for this page
            if table_tree != []:
                columns = table_tree[0].xpath('thead/tr/th')
                column_headings = [column.text for column in columns]

                for headings in column_headings:
                    row_dict = {}

                rows_tree = table_tree[0].xpath('tbody/tr')
                num_rows = len(rows_tree)

                for row in range(0,num_rows):
                    row_tree = rows_tree[row]
                    if row_tree != []:
                        #get profile ID and workout ID
                        workout_info_link = row_tree.xpath('td/a')[0].attrib["href"]
                        profile_ID = None
                        workout_ID = None

                        #get profile and workout IDs from workout link
                        if workout_info_link.split("/")[-2] == "individual" or workout_info_link.split("/")[-2] == "race":
                            profile_ID = workout_info_link.split("/")[-1]
                            workout_ID = workout_info_link.split("/")[-3]
                        else:
                            workout_ID = workout_info_link.split("/")[-2]

                        #get workout data from row
                        workouts[workout_ID] = C2Scrape.get_workout_data(row_tree, column_headings, ranking_table, profile_ID)
                        
                        if get_profile_data and profile_ID != None:
                            #add athlete profile object to thread queue
                            profile_queue.put(mw.Profile(profile_ID, "athlete", url_profile_base + profile_ID, athletes, athletes_cache, lock, s))
                            queue_added += 1

                        if get_extended_workout_data:
                            profile_queue.put(mw.Profile(workout_ID, "ext_workout", workout_info_link, ext_workouts, ext_workouts_cache, lock, s))
                            queue_added += 1

        #after each page, check to see if we should write to file
        if C2Scrape.check_write_buffer(timestamp_last_write, write_buffer):
            lock.acquire()
            C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
            if config["use_cache"]:
                C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])
            timestamp_last_write = datetime.now().timestamp()
            lock.release()

print("Finished scraping ranking tables, waiting for profile threads to finish...")

# wait for queue to be empty, then join the threads
while not profile_queue.empty():
    time.sleep(1)
    print("Queue size: " + str(profile_queue.qsize()))
    lock.acquire()
    if C2Scrape.check_write_buffer(timestamp_last_write, write_buffer):
        C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
        if config["use_cache"] == True:
            C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])
        timestamp_last_write = datetime.now().timestamp()
    lock.release()

#final write
C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
if config["use_cache"] == True:
    C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])

if profile_queue.empty():
    #join threads
    for i in range(THREADS):
        threads[i].join()



