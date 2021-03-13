import requests
from lxml import etree, html
import json
from datetime import datetime, date
from time import strftime,gmtime
import os
import shutil
import queue #multithreading
import threading
#object to store url and associated workout variables
class RankingPage():

    def __init__(self, base_url, year, machine, event, query_parameters={}):
        #query should be a dictionary of url query keys and values
        self.machine = machine
        self.base_url = base_url
        self.year = year
        self.event = event
        self.query_parameters = query_parameters
        self.url_parts = (base_url, year, machine, event)
        self.url_string = self.get_url_string()
    
    def get_url_string(self):
        #construct url string
        url_string = "/".join(map(str,self.url_parts)) + "?"
        #construct url with query string
        for key,val in self.query_parameters.items():
            if (val != None and val != "") and (key != None and key != ""):
                url_string = url_string + key + "=" + val + "&"
        return url_string.strip("&")

class Profile:
    #holds all the information needed for the worker threads to visit this profile and scrape data
    def __init__(self, profile_id, profile_type, url, profile_list, profile_cache, lock,session):
        self.profile_id = profile_id
        self.profile_type = profile_type
        self.url = url
        self.profile_list = profile_list
        self.profile_cache = profile_cache
        self.data = None #json object with the profile data
        self.lock = lock
        self.session = session

class ProfileThread(threading.Thread):
    #define how the threads function
    def __init__(self, name, profile_queue):
        threading.Thread.__init__(self)
        self.name = name
        self._stop_event = threading.Event()
        self.profile_queue = profile_queue

    def run(self):
        #execute on thread.start()
        print(f" ** Starting thread - {self.name}")

        while not self._stop_event.isSet():
            #thread will continuously check the queue for work until the master process joins the threads, and the stop_event signal is sent
            try:
                profile = self.profile_queue.get(block=False)

            except queue.Empty:
                pass

            else:
                #print("Thread " + self.name + ": Getting profile: " + profile.url)
                thread_get_profile(profile)

        print(f" ** Completed thread - {self.name}")

    
    def join(self, timeout=None):
        #send stop event to terminate the work loop before calling join
        self._stop_event.set()
        super().join(timeout)
        print(f" ** Joined thread - {self.name}")

def get_url(session, url, exception_on_error = False):
    try:
        r = session.get(url)
        if r.status_code == 200:
            return r
        else:
            if exception_on_error == False:
                return None
            else:
                raise ValueError("A server error occured, status code: " + str(r.status_code))
    except requests.exceptions.ConnectionError:
        if exception_on_error == False:
            return None
        else:
            raise ValueError("Could not access url: " + url)


def construct_url(url_parts, machine_parameters={}):
    #construct url string
    url = "/".join(url_parts) + "?"
    #construct url with query string
    for key,val in machine_parameters["query"].items():
        if (val != None and val != "") and (key != None and key != ""):
            url = url + key + "=" + val + "&"
    return url.strip("&")
    

def lists2dict(listkey,listval):
    #takes two lists, used the first as keys and the second as values, returns a dictionary
    returndict={}
    for key, val in zip(listkey, listval):
        returndict[key] = val
    return returndict

def generate_C2Ranking_urls(machine_parameters, url_years, url_base):
#this supports 4 query parameters for each machine type, the keys can be different, but exactly 4 must be present in the data structure below, the lists though can be blank
#can be increased by adding more nested for loops when constructing the query string
#TODO: to make this fully dynamic I think I need to use a recursive algorithm

    #generate URLS for scraping
    urls = []
    #this can be improved I think using recursion, try googling "recursive generator"
    for url_year in url_years:
        for machine_type_key, machine_type_values in machine_parameters.items():
            for url_event in machine_parameters[machine_type_key]["events"]:
                param_keys=[]
                for param_key,param_values in machine_type_values["query"].items():
                    #get all the parameter keys for this machine type
                    param_keys.append(param_key)
                    if len(param_values) == 0:
                        #safeguard against an empty entry, if nothing in list the below for loops will skip all the entries after
                        machine_type_values["query"][param_key] = [""]

                #now iterate through them and construct the URL
                for val0 in machine_parameters[machine_type_key]["query"][param_keys[0]]:
                    for val1 in machine_parameters[machine_type_key]["query"][param_keys[1]]:
                        for val2 in machine_parameters[machine_type_key]["query"][param_keys[2]]:
                            for val3 in machine_parameters[machine_type_key]["query"][param_keys[3]]:
                                query_parameters = lists2dict(param_keys,(val0,val1,val2,val3))
                                urls.append(RankingPage(url_base, url_year, machine_type_key, url_event, query_parameters))
    return urls

#get athlete or extended workout profile
def thread_get_profile(profile):
    #check if in cache.
    #Not too concerned about threads colliding here as worst case is that the thread makes an extra URL visit if the cache gets populated with this profile id in between this check and the url visit, profile will just be overwritten in dictionary with the same data
    if profile.profile_id in profile.profile_cache.keys():
        profile.data = profile.profile_cache[profile.profile_id]#retrieve from cache
    else:
        r = get_url(profile.session, profile.url)
        if r != None:
            if profile.profile_type == "athlete":
                profile.data = get_athlete_profile(r)
                profile.data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
            
            #TODO breakout into function
            if profile.profile_type == "ext_workout":
                profile.data = get_ext_workout_profile(r)
                profile.data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())

    profile.lock.acquire() #dict.update is thread safe but json.dumps is not, need to hold here when printing output
    profile.profile_list.update({profile.profile_id:profile.data})
    profile.profile_cache.update({profile.profile_id:profile.data})
    profile.lock.release()

def get_athlete_profile(r):
    #r: requests object
    tree = html.fromstring(r.text)
    #profile labels that are contained in <a> tags
    a_tag_labels = ["Affiliation:", "Team:"]

    athlete_profile = {}
    content = tree.xpath('//section[@class="content"]')
    athlete_profile["name"] = content[0].xpath('h2')[0].text
    athlete_profile_labels = content[0].xpath('p/strong')
    #store as list
    athlete_profile_labels = [label.text for label in athlete_profile_labels]

    i = 0
    #check to see if I need to be logged in
    if "You must be <a href=\"/login\">logged in</a> to see this user\'s profile" in r.text:
        athlete_profile["availablity"] = "logged in"
    elif "<div class=\"stats\">" in r.text:
        #stat boxes only appear when profile is accessible
        athlete_profile["availablity"] = "public"
    elif "This user's profile is only accessible to training partners." in r.text:
        athlete_profile["availablity"] = "training partner"
    else:
        athlete_profile["availablity"] = "private"

    #profile values not contained in tags so need to be a bit messy to get them
    for profile_label in athlete_profile_labels:
        #cycle through each profile label and search for the matching value
        if profile_label in a_tag_labels:
            profile_value = content[0].xpath('p/strong[contains(text(), "' + profile_label +'")]/following-sibling::a/text()')
        else:
            profile_value = content[0].xpath('p/strong[contains(text(), "' + profile_label +'")]/following-sibling::text()[1]')
        #clean up
        profile_label = profile_label.strip(":").lower()
        #add to profile dictionary
        athlete_profile[profile_label] = profile_value[0].strip(" ")

    return athlete_profile

def get_workout_data(row_tree, column_headings, ranking_table, profile_ID):
    workout_data = []
    row_data_tree = row_tree.xpath('td | td/a')
    del row_data_tree[1] #hacky, but to remove a row that shouldn't be their due to the /a tag used for the name parameter
    row_list = [x.text for x in row_data_tree]                    
    workout_data = lists2dict(map(str.lower, column_headings),row_list)
    workout_data["year"] = ranking_table.year
    workout_data["machine"] = ranking_table.machine
    workout_data["event"] = ranking_table.event
    workout_data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
    workout_data["profile_id"] = profile_ID
    for key, val in ranking_table.query_parameters.items():
        workout_data[key]=val
    return workout_data
    
def get_ext_workout_profile(r):
    #r: requests object
    tree = html.fromstring(r.text)
    label_tree = tree.xpath('/html/body/div/div/div[1]/strong')
    data_labels = [label.text for label in label_tree]
    profile = {}
    for data_label in data_labels:
        value = tree.xpath(f'/html/body/div/div/div[1]/strong[contains(text(), "{data_label}")]/following-sibling::text()[1]')
        label = data_label.strip(":").lower()
        profile[label] = value[0]

    return profile
    
def write_data(out_files, datas):
    for out_file, data in zip(out_files, datas):
        try:
            fw = open(out_file, "w")
            output_data = json.dumps(data, indent=2)
            fw.write(output_data)
            fw.close
            print("Write complete: " + out_file)
        except:
            print("Write failed: " + out_file + ". Press any key to continue")
            fl = open("log","a")
            fl.write("Write failed: " + out_file)
    return

def get_str_ranking_table_progress(queue_size, queue_added, ranking_url_count, num_ranking_urls, page,pages):
    return f"Queue size: {str(queue_size)}/{str(queue_added)} | Ranking Table: {str(ranking_url_count)}/{str(num_ranking_urls)} | Page: {str(page)}/{str(pages)} |"

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

def backup_file(path):
    if os.path.isfile(path):
        try:
            shutil.copyfile(path, path + "_backup")
        except:
            print("Could not back up: " + path)

def check_write_buffer(timestamp_last_write, write_buffer):
    return datetime.now().timestamp() > timestamp_last_write + write_buffer

def C2_login(session, url_login, username, password):
    login = session.get(url_login)
    login_tree = html.fromstring(login.text)
    hidden_inputs = login_tree.xpath(r'//form//input[@type="hidden"]')
    form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs} #get csrf token
    form['username'] = username
    form['password'] = password
    response = session.post(url_login, data=form)
    return response