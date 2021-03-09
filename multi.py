import C2_scrape_helpers as C2scrape
import string
import json
import datetime
import os #this and shutil used for checking for and making copies of files
import shutil
from lxml import etree, html
import threading

config = {}
try:
    fo = open("C2config_multi.json")
    config = json.load(fo)
    fo.close
except:
    print("Could not open config file. Quitting")
    quit()

write_buffer = config["write_buffer"] #write every X ranking pages
write_buffer_count = 1
get_extended_workout_data = config["get_extended_workout_data"]
get_profile_data = config["get_profile_data"]

# workouts_file = "C2Rankings_" + strftime("%d%m%Y_%H%M", gmtime()) + ".json"
# athletes_file = "C2Athletes_" + strftime("%d%m%Y_%H%M", gmtime()) + ".json"
# extended_file = "C2Extended_" + strftime("%d%m%Y_%H%M", gmtime()) + ".json"
workouts_file = config["workouts_file"]
athletes_file = config["athletes_file"]
extended_file = config["extended_file"]
athletes_cache_file = config["athletes_cache_file"]
extended_cache_file = config["extended_cache_file"]
url_profile_base = config["url_profile_base"]
urls_visited = 0

athlete_profiles = {}
workouts = {}
ex_workout_data = {}


urls = C2scrape.generate_C2Ranking_urls(config["url_query_parameters"], config["url_parameters"]["url_years"], config["url_parameters"]["url_events"], config["url_parameters"]["url_base"])

if os.path.isfile(workouts_file):
    shutil.copyfile(workouts_file, workouts_file + "_backup")

if os.path.isfile(athletes_file):
    shutil.copyfile(athletes_file, athletes_file + "_backup")

if os.path.isfile(extended_file):
    shutil.copyfile(extended_file, extended_file + "_backup")

if config["use_cache"] == True:
    try:
        fo = open(athletes_cache_file)
        athlete_profiles_cache = json.load(fo)
        fo.close
    except:
        print("Couldn't load athletes cache.")
        athlete_profiles_cache = {}

    try:
        fo = open(extended_cache_file)
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
        #visit each page using the master thread, then give each row to a thread
        #conceptually easier to implement at first then giving each page to a thread (though more overhead) as there should not be any duplicate workouts or profiles on a page and don't have to worry about adding duplicate entries to the datastructures but still give a big speed boost
        url_string = url.url_string + "&page=" + str(page)
        urls_visited = urls_visited + 1
        
        print(C2scrape.get_str_ranking_table_progress(urls_visited, ranking_url_count,num_ranking_urls,page,pages) + "Getting ranking page: " + url_string)
        if page > 1:
            #don't get the first page again (if page is ommitted, page 1 is loaded)
            workouts_page=[]
            r = C2scrape.get_url(url_string)

        if r != None:
            tree = html.fromstring(r.text)
            table_tree = tree.xpath('//html/body/div[2]/div/main/section[@class="content"]/table')
            
            #get column headings
            if table_tree != []:
                columns = table_tree[0].xpath('thead/tr/th')
                column_headings = [column.text for column in columns]

                for headings in column_headings:
                    row_dict = {}

                num_rows = int(config["columns_per_page"])

                #now we have the headers for the page, can mutlithread going through the rows
                for row in range(1,num_rows+1):
                    row_tree = table_tree[0].xpath('tbody/tr[' + str(row) + ']')
                    if row_tree != []:
                        #TODO: refactor this so print strings inside loop don't need as many variables
                        workout_data, ex_workout_data_profile, athlete_profile, profile_ID, workout_ID, urls_visited = C2scrape.get_workout_from_ranking_table_row(row_tree, url, column_headings, urls_visited, ranking_url_count, num_ranking_urls, page, pages, row, num_rows, get_extended_workout_data, get_profile_data, ex_workout_data_cache,athlete_profiles_cache, url_profile_base)                                
                        #update global lists           
                        if athlete_profile != None:
                            athlete_profiles[profile_ID] = athlete_profile
                            athlete_profiles_cache[profile_ID] = athlete_profile    
                        if ex_workout_data_profile != None:
                            ex_workout_data_cache[workout_ID] = ex_workout_data_profile
                            ex_workout_data[workout_ID] = ex_workout_data_profile  
                        if workout_data != []:
                            workouts[workout_ID] = workout_data
                    

            #at the end of a page, check to see if we should write to file
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