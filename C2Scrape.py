import requests
from lxml import etree, html
import json
from datetime import datetime, date
from time import strftime,gmtime
import os
import shutil
from lxml import etree, html #reading html 

class Data():

    def __init__(self, config):
        self.athletes = {}
        self.workouts = {}
        self.ext_workouts = {}
        self.list = [self.athletes, self.workouts, self.ext_workouts]
        self.files = DataFiles(config)
        self.files.set_data(self)


class DataFiles():
    
    def __init__(self, config):
        self.workouts = config["workouts_file"]
        self.athletes = config["athletes_file"]
        self.extended = config["extended_file"]
        self.list = [self.workouts, self.athletes, self.extended]
        self.timestamp_last_write = 0
        self.write_buffer = config["write_buffer"] #write every X ranking pages
        #backup previous output
        self.backup_files()
        self.init_files()

    def set_data(self, data):
        self.data = data

    def write(self, data, lock=None):
        if check_write_buffer(timestamp_last_write, write_buffer):
            if lock != None:
                lock.acquire()

            for out_file, data in zip(self.list, data.list):
                try:
                    fw = open(out_file, "w")
                    output_data = json.dumps(data, ensure_ascii = False)
                    fw.write(output_data)
                    fw.close
                    print("Write complete: " + out_file)
                except:
                    print("Write failed: " + out_file)
                    fl = open("log","a+")
                    fl.write("Write failed: " + out_file)

            if lock != None:
                lock.release()

            self.timestamp_last_write = datetime.now().timestamp()

    def backup_files(self):
        for path in self.list:
            if os.path.isfile(path):
                try:
                    shutil.copyfile(path, path + "_backup")
                except:
                    print("Could not back up: " + path)

    def init_files(self):
        for path in self.list:
            try:
                fw = open(path, "w+")
                fw.close
            except:
                print("Init failed: " + path)
                fl = open("log","a+")
                fl.write("Init failed: " + path)

class Cache():

    def __init__(self, config):
        try:
            self.files = CacheFiles(config)
            self.athletes = self.files.load(config["athletes_cache_file"])
            self.ext_workouts = self.files.load(config["extended_cache_file"])
        except :
            print("Couldn't load cache files:" )
            self.athletes = {}
            self.ext_workouts = {} 
        
class CacheFiles():
    
    def __init__(self, config):
        self.athletes = config["athletes_cache_file"]
        self.extended = config["extended_cache_file"]
        self.list = [self.athletes, self.extended]
        self.timestamp_last_write = 0
        self.write_buffer = config["write_buffer"] #write every X ranking pages
        #backup previous output
        self.backup_files()

    def load(self, path):
        cache = {}
        try:
            fo = open(path)
            cache = json.load(fo)
            fo.close
            print(f"Loaded cache file: {path}")
        except:
            print(f"Couldn't load the cache file: {path}")
            cache = {}
        finally:
            return cache 

    def write(self, cache, lock=None):
        if check_write_buffer(timestamp_last_write, write_buffer) and config["use_cache"]:
            if lock != None:
                lock.acquire()

            for out_file, data in zip(self.list, data.list):
                try:
                    fw = open(out_file, "a+")
                    output_data = json.dumps(data, ensure_ascii = False)
                    fw.write(output_data)
                    fw.close
                    print("Write complete: " + out_file)
                except:
                    print("Write failed: " + out_file)
                    fl = open("log","a+")
                    fl.write("Write failed: " + out_file)

            self.timestamp_last_write = datetime.now().timestamp()
            if lock != None:
                lock.release()

    def backup_files(self):
        for path in self.list:
            if os.path.isfile(path):
                try:
                    shutil.copyfile(path, path + "_backup")
                except:
                    print("Could not back up: " + path)




class RankingPage():
    """Object to store url and associated workout variables"""

    def __init__(self, base_url, year, machine, event, config, threads, data, cache=None, query_parameters={}):
        #query should be a dictionary of url query keys and values
        self.machine = machine
        self.base_url = base_url
        self.year = year
        self.event = event
        self.query_parameters = query_parameters
        self.url_parts = (base_url, year, machine, event)
        self.url_string = self.get_url_string()
        self.config = config
        self.threads = threads
        self.data = data
        self.cache = cache

    def get_url_string(self):
        #construct url string
        url_string = "/".join(map(str,self.url_parts)) + "?"
        #construct url with query string
        for key,val in self.query_parameters.items():
            if (val != None and val != "") and (key != None and key != ""):
                url_string = url_string + key + "=" + val + "&"
        return url_string.strip("&")

    def scrape(self, ranking_table_count, queue_added, num_ranking_tables):
        r = get_url(threads.session, self.url_string)
        
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
                url_string = self.url_string + "&page=" + str(page)

                print(get_str_ranking_table_progress(threads.job_queue.qsize(), queue_added, ranking_table_count, num_ranking_tables, page,pages) + "Getting ranking page: " + url_string)
                if page > 1:
                    #don't get the first page again (if page is ommitted, page 1 is loaded)
                    workouts_page=[]
                    r = get_url(s, url_string)
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
                                data.workouts[workout_ID] = get_workout_data(row_tree, column_headings, self, profile_ID)
                                
                                if config["get_profile_data"] and profile_ID != None:
                                    #add athlete profile object to thread queue
                                    threads.job_queue.put(mw.Job(get_athlete, url_profile_base + profile_ID, [athletes, athletes_cache, profile_ID]))
                                    queue_added += 1

                                if config["get_extended_workout_data"]:
                                    threads.job_queue.put(mw.Job(Cget_ext_workout, workout_info_link, [ext_workouts, ext_workouts_cache, workout_ID]))
                                    queue_added += 1

                #after each page, check to see if we should write to file
                if check_write_buffer(timestamp_last_write, write_buffer):
                    threads.lock.acquire()
                    write_data([workouts_file, athletes_file, extended_file],[workouts, athletes, ext_workouts])
                    if config["use_cache"]:
                        write_data([athletes_cache_file, extended_cache_file],[athletes_cache, ext_workouts_cache])
                    timestamp_last_write = datetime.now().timestamp()
                    threads.lock.release()


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

def generate_ranking_pages(config, threads, data, cache):

    machine_parameters = config["machine_parameters"]
    url_years = config["url_parameters"]["url_years"]
    url_base = config["url_parameters"]["url_base"]
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
                                urls.append(RankingPage(url_base, url_year, machine_type_key, url_event, config, threads, data, cache, query_parameters))
    return urls

def get_athlete_data(r):
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
        athlete_profile["availablity"] = "available"
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
    
def get_ext_workout_data(r):
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
    


def get_str_ranking_table_progress(queue_size, queue_added, ranking_url_count, num_ranking_urls, page,pages):
    return f"Queue size: {str(queue_size)}/{str(queue_added)} | Ranking Table: {str(ranking_url_count)}/{str(num_ranking_urls)} | Page: {str(page)}/{str(pages)} |"



def check_write_buffer(timestamp_last_write, write_buffer):
    return datetime.now().timestamp() > timestamp_last_write + write_buffer

def C2_login(session, url_login, username, password, url_login_success):
    login = session.get(url_login)
    login_tree = html.fromstring(login.text)
    hidden_inputs = login_tree.xpath(r'//form//input[@type="hidden"]')
    form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs} #get csrf token
    form['username'] = username
    form['password'] = password
    response = session.post(url_login, data=form)
    if response.url != url_login_success:
        sys.exit("Unable to login to the logbook, quitting.")
    else:
        print("Login")
    return session
    
    return response

def get_athlete(job):
    #TODO these job functions will fail fairly silently (error prints will get swallowed up by other console output) if a none 200 response code or on connection error
    #function executed by thread, updates cache and data dictionary

    job_data = {}
    athletes = job.custom_data[0]
    cache = job.custom_data[1]
    profile_id = job.custom_data[2]

    #check if already in data dictionary, if so, do nothing
    if profile_id not in athletes.keys():
        #check if in cache.
        if profile_id in cache.keys():
            job_data = cache[profile_id]#retrieve from cache
        else:
            get_url_success = job.get_url() #get the URL
            if get_url_success:
                if job.request.status_code == 200: #check that the URL was recieved OK
                    job_data = get_athlete_data(job.request)
                    job_data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
                    job.lock.acquire()
                    cache.update({profile_id:job_data}) #cache
                    job.lock.release()
                else:
                    print(f"There was a problem with {job.url}, status code: {job.request.status_code}")

        job.lock.acquire() #dict.update is thread safe but other fucntions used elsewhere (e.g. json.dumps) may not, need lock here
        athletes.update({profile_id:job_data}) #main data
        job.lock.release()

def get_ext_workout(job):
    #function executed by thread, updates cache and data dictionary

    job_data = {}
    ext_workouts = job.custom_data[0]
    cache = job.custom_data[1]
    workout_id = job.custom_data[2]

    #check if already in data dictionary, if so, do nothing
    if workout_id not in ext_workouts.keys():
        #check if in cache.
        if workout_id in cache.keys():
            job_data = cache[workout_id]#retrieve from cache
        else:
            get_url_success = job.get_url() #get the URL
            if get_url_success:
                if job.request.status_code == 200: #check that the URL was recieved OK
                        job_data = get_ext_workout_data(job.request)
                        job_data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
                        job.lock.acquire() #dict.update is thread safe but other fucntions used elsewhere (e.g. json.dumps) may not, need lock here
                        cache.update({workout_id:job_data}) #cache
                        job.lock.release()
                else:
                    print(f"There was a problem with {job.url}, status code: {job.request.status_code}")

        job.lock.acquire() #dict.update is thread safe but other fucntions used elsewhere (e.g. json.dumps) may not, need lock here
        ext_workouts.update({workout_id:job_data}) #main data
        job.lock.release()

def load_config(path):
    try:
        fo = open("C2config.json")
        return json.load(fo)
        fo.close
    except:
        print("Could not open config file. Quitting")
        quit()

    