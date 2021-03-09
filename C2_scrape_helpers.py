import requests
from lxml import etree, html
import json
from time import strftime,gmtime

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


def get_url(url, exception_on_error = False):
    try:
        r = requests.get(url)
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


def construct_url(url_parts, url_query_parameters={}):
    #construct url string
    url = "/".join(url_parts) + "?"
    #construct url with query string
    for key,val in url_query_parameters.items():
        if (val != None and val != "") and (key != None and key != ""):
            url = url + key + "=" + val + "&"
    return url.strip("&")
    

def lists2dict(listkey,listval):
    returndict={}
    for key, val in zip(listkey, listval):
        returndict[key] = val
    return returndict


def generate_C2Ranking_urls(url_query_parameters, url_years, url_events, url_base):
#this supports 4 parameters for each machine type, they can be different, but exactly 4 must be present in the data structure below, the lists though can be blank
#can be increased by adding more nested for loops when constructing the query string
#TODO: to make this fully dynamic I think I need to use a recursive algorithm

    #generate URLS for scraping
    urls = []
    #this can be improved I think using recursion, try googling "recursive generator"
    for url_year in url_years:
        for url_event in url_events:
            for machine_type_key, machine_type_values in url_query_parameters.items():
                param_keys=[]
                for param_key,param_values in machine_type_values.items():
                    #get all the parameter keys for this machine type
                    param_keys.append(param_key)
                for val0 in url_query_parameters[machine_type_key][param_keys[0]]:
                    for val1 in url_query_parameters[machine_type_key][param_keys[1]]:
                        for val2 in url_query_parameters[machine_type_key][param_keys[2]]:
                            for val3 in url_query_parameters[machine_type_key][param_keys[3]]:
                                urls.append(RankingPage(url_base, url_year, machine_type_key, url_event,lists2dict(param_keys,(val0,val1,val2,val3))))
    return urls

def get_athlete_profile(request):

    tree = html.fromstring(request.text)
    a_tag_labels = ["Affiliation:", "Team:"]

    athlete_profile = {}
    content = tree.xpath('//section[@class="content"]')
    athlete_profile["name"] = content[0].xpath('h2')[0].text
    athlete_profile_labels = content[0].xpath('p/strong')
    #store as list
    athlete_profile_labels = [label.text for label in athlete_profile_labels]

    i = 0
    #check to see if I need to be logged in
    if "You must be <a href=\"/login\">logged in</a> to see this user\'s profile" in request.text:
        athlete_profile["availablity"] = "logged in"
    elif "<div class=\"stats\">" in request.text:
        #stat boxes only appear when profile is accessible
        athlete_profile["availablity"] = "public"
    elif "This user's profile is only accessible to training partners." in request.text:
        athlete_profile["availablity"] = "training partner"
    else:
        athlete_profile["availablity"] = "private"
    #check if I need to be a training partner




    #profile values not contained in tags so need to be a bit messy to get them
    for profile_label in athlete_profile_labels:
        #cycle through each profile label and search for the matching value
        #if in a label that is known to be in an a_tag
        if profile_label in a_tag_labels:
            profile_value = content[0].xpath('p/strong[contains(text(), "' + profile_label +'")]/following-sibling::a/text()')
        else:
            profile_value = content[0].xpath('p/strong[contains(text(), "' + profile_label +'")]/following-sibling::text()[1]')
        #clean up
        profile_label = profile_label.strip(":").lower()
        #add to profile dictionary
        athlete_profile[profile_label] = profile_value[0].strip(" ")


    return athlete_profile

def write_data(out_files, datas):
    for out_file, data in zip(out_files, datas):
        fw = open(out_file, "w")
        fw.write(json.dumps(data, indent=2))
        fw.close
    return

def get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, row, rows):
    return get_str_ranking_table_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages) + "Row: " + str(row) + "/" + str(rows) + " | "

def get_str_ranking_table_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages):
    return "URLs visited: " +  str(urls_visited) + " | " + "Ranking Table: " + str(ranking_url_count) + "/" + str(num_ranking_urls) + " | " + "Page: " + str(page) + "/" + str(pages) + " | "

def get_workout_from_ranking_table_row (row_tree, url, column_headings, urls_visited, ranking_url_count, num_ranking_urls, page, pages, row, num_rows, get_extended_workout_data, get_profile_data,ex_workout_data_cache, athlete_profiles_cache, url_profile_base):

    rows = row_tree[0].xpath('td | td/a')
    del rows[1] #hacky, but to remove a row that shouldn't be their due to the /a tag used for the name
    row_list = [row.text for row in rows]
    workout_info_link_tree = row_tree[0].xpath('td/a')[0].attrib["href"]
    
    profile_ID = None
    workout_ID = None
    athlete_profile = None
    ex_workout_data_profile = None
    workout_data = []
    #extract profile_ID from URL
    #check the format of the url, some don't have a profileID on the end of them
    if workout_info_link_tree.split("/")[-2] == "individual" or workout_info_link_tree.split("/")[-2] == "race":
        profile_ID = workout_info_link_tree.split("/")[-1]
        workout_ID = workout_info_link_tree.split("/")[-3]
    else:
        workout_ID = workout_info_link_tree.split("/")[-2]

    workout_data = lists2dict(map(str.lower, column_headings),row_list)
    workout_data["year"] = url.year
    workout_data["machine"] = url.machine
    workout_data["event"] = url.event
    workout_data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
    workout_data["profile_id"] = profile_ID
    for key, val in url.query_parameters.items():
        workout_data[key]=val

    #TODO break these two sections out into two seperate functions, needs work on the string printing bit to help                
    if get_extended_workout_data == True:
        if workout_ID in ex_workout_data_cache.keys():
            print(get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(row), num_rows) + "Found extended workout data in cache: " + str(workout_ID))
            ex_workout_data_profile = ex_workout_data_cache[workout_ID]
        else:
            urls_visited = urls_visited + 1
            print(get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(row), num_rows) +  "Getting extended workout data: " + workout_info_link_tree)
            r_workout = get_url(workout_info_link_tree)

            #TODO implment expiry on cache?
            if r_workout != None:
                ex_workout_tree = html.fromstring(r_workout.text)
                ex_workout_data_labels = ex_workout_tree.xpath('/html/body/div/div/div[1]/strong')
                ex_workout_data_labels = [label.text for label in ex_workout_data_labels]
                ex_workout_data_profile = {}
                for ex_workout_data_label in ex_workout_data_labels:
                    ex_workout_value = ex_workout_tree.xpath('/html/body/div/div/div[1]/strong[contains(text(), "' + ex_workout_data_label +'")]/following-sibling::text()[1]')
                    ex_workout_data_label = ex_workout_data_label.strip(":").lower()
                    ex_workout_data_profile[ex_workout_data_label] = ex_workout_value[0]#, "date_cached": datetime.datetime.now()} datetime doesn't JSON?
                ex_workout_data_profile["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())

    if get_profile_data == True and profile_ID != None: 
            if profile_ID in athlete_profiles_cache.keys():
                print(get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(row), num_rows) + "Found profile in cache: " + str(profile_ID))
                athlete_profile = athlete_profiles_cache[profile_ID]
            else:
                #visit profile page and grab info
                profile_url = url_profile_base + profile_ID
                urls_visited = urls_visited + 1
                print(get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(row), num_rows) + "Getting profile: " + profile_url)
                r_profile = get_url(profile_url)
                if r_profile != None:
                    athlete_profile = get_athlete_profile(r_profile)
                    athlete_profile["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
    return workout_data, ex_workout_data_profile, athlete_profile, profile_ID, workout_ID, urls_visited