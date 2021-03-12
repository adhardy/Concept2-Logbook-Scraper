import C2Scrape
import string
import json
from datetime import datetime, date
import os #this and shutil used for checking for and making copies of files
import shutil #copying for backups
from lxml import etree, html #reading html 
import queue #multithreading
import threading
from time import strftime,gmtime
import time #sleep

class Profile:
    def __init__(self, profile_id, profile_type, url, profile_list, profile_cache):
        self.profile_id = profile_id
        self.profile_type = profile_type
        self.url = url
        self.profile_list = profile_list
        self.profile_cache = profile_cache
        self.data = None #json object with the profile data

#get athlete or extended workout profile
def get_profile(profile):
    #check if in cache.
    #Not too concerned about threads colliding here as worst case is that the thread makes an extra URL visit if the cache gets populated with this profile id in between this check and the url visit, profile will just be overwritten in dictionary with the same data
    if profile.profile_id in profile.profile_cache.keys():
        profile.data = profile.profile_cache[profile.profile_id]#retrieve from cache
    else:
        r = C2Scrape.get_url(profile.url)
        if r != None:
            if profile.profile_type == "athlete":
                profile.data = C2Scrape.get_athlete_profile(r)
                profile.data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
            
            #TODO breakout into function
            if profile.profile_type == "ext_workout":
                profile.data = C2Scrape.get_ext_workout_profile(r)
                profile.data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())

        lock.acquire()
        profile.profile_list.update({profile.profile_id:profile.data})
        profile.profile_cache.update({profile.profile_id:profile.data})
        lock.release()

# Class
class MultiThread(threading.Thread):
    def __init__(self, name, profile_queue):
        threading.Thread.__init__(self)
        self.name = name
        self._stop_event = threading.Event()

    def run(self):
        print(f" ** Starting thread - {self.name}")

        while not self._stop_event.isSet():
            try:
                profile = profile_queue.get(block=False)

            except queue.Empty:
                pass

            else:
                #print("Thread " + self.name + ": Getting profile: " + profile.url)
                get_profile(profile)

        print(f" ** Completed thread - {self.name}")

    
    def join(self, timeout=None):
        """set stop event and join within a given time period"""
        self._stop_event.set()
        super().join(timeout)

def backup_file(path):
    if os.path.isfile(path):
        try:
            shutil.copyfile(path, path + "_backup")
        except:
            print("Could not back up: " + path)

def load_cache(cache_file):
    #cache path on file system, and python dictionary where the cache will be loaded to
    cache = []
    try:
        fo = open(cache_file)
        cache = json.load(fo)
        fo.close
        print(f"Loaded cache file: {cache_file}")
    except:
        print(f"Couldn't load the cache file: {cache_file}")
        cache = {}
    finally:
        return cache

config = {}
profile_queue = queue.Queue()
try:
    fo = open("C2config.json")
    config = json.load(fo)
    fo.close
except:
    print("Could not open config file. Quitting")
    quit()

# initializing threads
THREADS = config["threads"]
threads = []
for i in range(THREADS):
    threads.append(MultiThread(str(i), profile_queue))


# start the threads
for i in range(THREADS): #TODO update all these loops with len(threads)
    threads[i].start()
    
lock = threading.Lock()

write_buffer = config["write_buffer"] #write every X ranking pages
write_buffer_count = 1
get_extended_workout_data = config["get_extended_workout_data"]
get_profile_data = config["get_profile_data"]

workouts_file = config["workouts_file"]
athletes_file = config["athletes_file"]
extended_file = config["extended_file"]
athletes_cache_file = config["athletes_cache_file"]
extended_cache_file = config["extended_cache_file"]
url_profile_base = config["url_profile_base"]
verbose = config["verbose"]

athletes = {}
workouts = {}
ext_workouts = {}
       
backup_file(workouts_file)
backup_file(athletes_file)
backup_file(extended_file)
backup_file(athletes_cache_file)
backup_file(extended_cache_file)

if config["use_cache"] == True:
    athletes_cache = load_cache(athletes_cache_file)
    ext_workouts_cache = load_cache(extended_cache_file)
else:
    athletes_cache = {}
    ext_workouts_cache = {}

ranking_tables = C2Scrape.generate_C2Ranking_urls(config["url_query_parameters"], config["url_parameters"]["url_years"], config["url_parameters"]["url_events"], config["url_parameters"]["url_base"])
num_ranking_tables = len(ranking_tables)

if config["max_ranking_tables"] != "":
    num_ranking_tables = int(config["max_ranking_tables"])-1

#initialize files
C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
if config["use_cache"] == "True":
    C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athlete_profiles_cache, ext_workouts_cache])
timestamp_last_write = datetime.now().timestamp()

ranking_table_count = 0 #counts the number of ranking table objects processed
queue_added = 0 #counts the total number of objects added to the queue
for ranking_table in ranking_tables[0:num_ranking_tables+1]: 
    ranking_table_count += 1
    r = C2Scrape.get_url(ranking_table.url_string)

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
        #master process loop over each page
        url_string = ranking_table.url_string + "&page=" + str(page)

        
        print(C2Scrape.get_str_ranking_table_progress(profile_queue.qsize(), queue_added, ranking_table_count,num_ranking_tables,page,pages) + "Getting ranking page: " + url_string)
        if page > 1:
            #don't get the first page again (if page is ommitted, page 1 is loaded)
            workouts_page=[]
            r = C2Scrape.get_url(url_string)
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
                        workout_data = []
                        row_data_tree = row_tree.xpath('td | td/a')
                        del row_data_tree[1] #hacky, but to remove a row that shouldn't be their due to the /a tag used for the name
                        row_list = [x.text for x in row_data_tree]                    
                        workout_data = C2Scrape.lists2dict(map(str.lower, column_headings),row_list)
                        workout_data["year"] = ranking_table.year
                        workout_data["machine"] = ranking_table.machine
                        workout_data["event"] = ranking_table.event
                        workout_data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
                        workout_data["profile_id"] = profile_ID
                        for key, val in ranking_table.query_parameters.items():
                            workout_data[key]=val
                        workouts[workout_ID] = workout_data
                        
                        if get_profile_data == True and profile_ID != None:
                            #add athlete profile object to thread queue
                            profile_queue.put(Profile(profile_ID, "athlete", url_profile_base + profile_ID, athletes, athletes_cache))
                            queue_added += 1

                        if get_extended_workout_data == True:
                            profile_queue.put(Profile(workout_ID, "ext_workout", workout_info_link, ext_workouts, ext_workouts_cache))
                            queue_added += 1

        #after each page, check to see if we should write to file
        if datetime.now().timestamp() > timestamp_last_write + write_buffer:
            lock.acquire()
            C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
            if config["use_cache"] == True:
                C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])
            timestamp_last_write = datetime.now().timestamp()
            lock.release()

print("Finished scraping ranking tables, waiting for profile threads to finish...")

# wait for queue to be empty, then join the threads
while profile_queue.empty() == False:
    time.sleep(1)
    print("Queue size: " + str(profile_queue.qsize()))
    lock.acquire()
    if datetime.now().timestamp() > timestamp_last_write + write_buffer:
        C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
        if config["use_cache"] == True:
            C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])
        timestamp_last_write = datetime.now().timestamp()
    lock.release()

if profile_queue.empty():
    #join threads
    for i in range(THREADS):
        threads[i].join()

#final write
C2Scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
if config["use_cache"] == True:
    C2Scrape.write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])

