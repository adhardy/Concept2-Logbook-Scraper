import C2_scrape_helpers as C2scrape
import string
import json
import datetime
import os #this and shutil used for checking for and making copies of files
import shutil
from lxml import etree, html
from time import strftime,gmtime

write_buffer = 1 #write every X ranking pages
write_buffer_count = 1
get_extended_workout_data = True
get_profile_data = True

# workouts_file = "C2Rankings_" + strftime("%d%m%Y_%H%M", gmtime()) + ".json"
# athletes_file = "C2Athletes_" + strftime("%d%m%Y_%H%M", gmtime()) + ".json"
# extended_file = "C2Extended_" + strftime("%d%m%Y_%H%M", gmtime()) + ".json"
workouts_file = "C2Rankings.json"
athletes_file = "C2Athletes.json"
extended_file = "C2Extended.json"
athletes_cache_file = "C2Athletes_cache.json"
extended_cache_file = "C2Extended_cache.json"
url_profile_base = "https://log.concept2.com/profile/"
urls_visited = 0
#TODO: improving caching behaviour: create dedicated cache files alongside data files
#cache files should load into a cache data structure, append any new info when found and write back to cache
#data files should only contain this runs data

athlete_profiles = {}
workouts = {}
ex_workout_data = {}
config = {}

try:
    fo = open("C2config.json")
    config = json.load(fo)
    fo.close
except:
    print("Could not open config file. Quitting")
    quit()

urls = C2scrape.generate_C2Ranking_urls(config["url_query_parameters"], config["url_parameters"]["url_years"], config["url_parameters"]["url_events"], config["url_parameters"]["url_base"])

#put all output files in folder
os.chdir("./output")

#TODO: if output files exist, copy them as backup
if os.path.isfile(workouts_file):
    shutil.copyfile(workouts_file, workouts_file + "_backup")

if os.path.isfile(athletes_file):
    shutil.copyfile(athletes_file, athletes_file + "_backup")

if os.path.isfile(extended_file):
    shutil.copyfile(extended_file, extended_file + "_backup")

if config["use_cache"] == True:
    try:
        fo = open("C2Athletes_cache.json")
        athlete_profiles_cache = json.load(fo)
        fo.close
    except:
        print("Couldn't load athletes cache.")
        athlete_profiles_cache = {}

    # try:
    #     fo = open("C2Rankings.json")
    #     workouts_cache = json.load(fo)
    #     fo.close
    # except:
    #     print("Couldn't load workout cache.")
    #     workouts_cache = {}

    try:
        fo = open("C2Extended_cache.json")
        ex_workout_data_cache = json.load(fo)
        fo.close
    except:
        print("Couldn't load extended workout cache.")
        ex_workout_data_cache = {}
else:
        athlete_profiles_cache = {}
        ex_workout_data_cache = {}

num_ranking_urls = len(urls)
if config["max_ranking_urls"] != "":
    num_ranking_urls = int(config["max_ranking_urls"])

ranking_url_count = 0 
for url in urls[0:num_ranking_urls+1]:
    r = C2scrape.get_url(url.url_string)
    ranking_url_count = ranking_url_count + 1
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
        url_string = url.url_string + "&page=" + str(page)
        urls_visited = urls_visited + 1
        
        print(C2scrape.get_str_ranking_table_progress(urls_visited, ranking_url_count,num_ranking_urls,page,pages) + "Getting ranking page: " + url_string)
        if page > 1:
            #don't get the first page again (if page is ommitted, page 1 is loaded)
            workouts_page=[]
            r = C2scrape.get_url(url_string)

        if r != None:
            tree = html.fromstring(r.text)
            table = tree.xpath('//html/body/div[2]/div/main/section[@class="content"]/table')
            
            #get column headings
            if table != []:
                columns = table[0].xpath('thead/tr/th')
                column_headings = [column.text for column in columns]

                for headings in column_headings:
                    row_dict = {}

                num_rows = int(config["columns_per_page"])
                for i in range(1,num_rows+1):

                    table_body = table[0].xpath('tbody/tr[' + str(i) + ']')
                    if table_body != []:
                        rows = table_body[0].xpath('td | td/a')
                        del rows[1] #hacky, but to remove a row that shouldn't be their due to the /a tag used for the name
                        row_list = [row.text for row in rows]
                        workout_info_link = table_body[0].xpath('td/a')[0].attrib["href"]
                        
                        profile_ID = None
                        workout_ID = None
                        athlete_profile = None
                        #extract profile_ID from URL
                        #check the format of the url, some don't have a profileID on them
                        if workout_info_link.split("/")[-2] == "individual" or workout_info_link.split("/")[-2] == "race":
                            profile_ID = workout_info_link.split("/")[-1]
                            workout_ID = workout_info_link.split("/")[-3]
                        else:
                            workout_ID = workout_info_link.split("/")[-2]

                        workout_data = []
                        workout_data = C2scrape.lists2dict(map(str.lower, column_headings),row_list)
                        workout_data["year"] = url.year
                        workout_data["machine"] = url.machine
                        workout_data["event"] = url.event
                        workout_data["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
                        workout_data["profile_id"] = profile_ID
                        for key, val in url.query_parameters.items():
                            workout_data[key]=val
                        workouts[workout_ID] = workout_data
                                               
                        if get_extended_workout_data == True:
                            if workout_ID in ex_workout_data_cache.keys():
                                print(C2scrape.get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(i), num_rows) + "Found extended workout data in cache: " + str(workout_ID))
                                ex_workout_data_temp = ex_workout_data_cache[workout_ID]
                            else:
                                urls_visited = urls_visited + 1
                                print(C2scrape.get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(i), num_rows) +  "Getting extended workout data: " + workout_info_link)
                                r_workout = C2scrape.get_url(workout_info_link)
                    
                                #TODO implment expiry on cache?
                                if r_workout != None:
                                    ex_workout_tree = html.fromstring(r_workout.text)
                                    ex_workout_data_labels = ex_workout_tree.xpath('/html/body/div/div/div[1]/strong')
                                    ex_workout_data_labels = [label.text for label in ex_workout_data_labels]
                                    ex_workout_data_temp = {}
                                    for ex_workout_data_label in ex_workout_data_labels:
                                        ex_workout_value = ex_workout_tree.xpath('/html/body/div/div/div[1]/strong[contains(text(), "' + ex_workout_data_label +'")]/following-sibling::text()[1]')
                                        ex_workout_data_label = ex_workout_data_label.strip(":").lower()
                                        ex_workout_data_temp[ex_workout_data_label] = ex_workout_value[0]#, "date_cached": datetime.datetime.now()} datetime doesn't JSON?
                                    ex_workout_data_temp["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
                            ex_workout_data_cache[workout_ID] = ex_workout_data_temp
                            ex_workout_data[workout_ID] = ex_workout_data_temp
                        if get_profile_data == True and profile_ID != None: 
                                if profile_ID in athlete_profiles_cache.keys():
                                    print(C2scrape.get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(i), num_rows) + "Found profile in cache: " + str(profile_ID))
                                    athlete_profile = athlete_profiles_cache[profile_ID]
                                else:
                                    #visit profile page and grab info
                                    profile_url = url_profile_base + profile_ID
                                    urls_visited = urls_visited + 1
                                    print(C2scrape.get_str_row_progress(urls_visited, ranking_url_count, num_ranking_urls, page,pages, str(i), num_rows) + "Getting profile: " + profile_url)
                                    r_profile = C2scrape.get_url(profile_url)
                                    if r_profile != None:
                                        athlete_profile = C2scrape.get_athlete_profile(r_profile)
                                        athlete_profile["retrieved"] = strftime("%d-%m-%Y %H:%M:%S", gmtime())
                                        athlete_profiles[profile_ID] = athlete_profile
                                        athlete_profiles_cache[profile_ID] = athlete_profile
                                #TODO: add info from profile to workout..or do this later after scraping?
                    
            if write_buffer_count % write_buffer == 0:
                C2scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athlete_profiles, ex_workout_data])
                if config["use_cache"] == "True":
                    C2scrape.write_data([athletes_cache_file, extended_cache_file],[athlete_profiles_cache, ex_workout_data_cache])
            write_buffer_count = write_buffer_count + 1

#final write
C2scrape.write_data([workouts_file, athletes_file, extended_file],[workouts, athlete_profiles, ex_workout_data])
if bool(config["use_cache"]) == True:
    C2scrape.write_data([athletes_cache_file, extended_cache_file],[athlete_profiles_cache, ex_workout_data_cache])
print("Visited " + str(urls_visited) +  " urls!")