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

class Scraper():

    def __init__(self, config_path):
        self.config = C2Scrape.load_config(config_path)
        #initialise data structures and output files
        self.data = C2Scrape.Data(self.config)
        if self.config["use_cache"] == True:
            self.cache = C2Scrape.Cache(self.config)
        else:
            cache=None

        # initialize threads
        self.threads = mw.MultiWebbing(self.config["threads"])

        #use same session as threads, log in to the website
        self.s = self.threads.session
        if self.config["C2_login"]:
            #TODO move loading of username password to environment vars rather than config file
            C2Scrape.C2_login(self.s, self.config["url_login"], self.config["C2_username"], self.config["C2_password"], "https://log.concept2.com/log")

        # start threads
        self.threads.start()

        #generate urls to visit
        self.ranking_tables = C2Scrape.generate_ranking_pages(self.config, self.threads, self.data, self.cache)
        self.num_ranking_tables = len(self.ranking_tables)

        #check for override of maximum ranking tables
        if self.config["max_ranking_tables"] != "":
             self.num_ranking_tables = int(config["max_ranking_tables"])

        self.ranking_table_count = 0 #counts the number of ranking table objects processed
        self.queue_added = 0 #counts the total number of objects added to the queue

    def scrape(self):

        #main loop for master process over each ranking table
        for ranking_table in self.ranking_tables[0:self.num_ranking_tables]: 
            self.ranking_table_count += 1
            ranking_table.scrape(self.ranking_table_count, self.queue_added, self.num_ranking_tables)

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

if __name__ == "__main__":
    scraper = Scraper("C2config.json")
    scraper.scrape()