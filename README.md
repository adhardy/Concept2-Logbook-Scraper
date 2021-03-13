# Concept2 Logbook Scraper

Scrapes the Concept2 Logbook site (log.concept2.com) and saves the information in JSON format. Uses multi-threading to spead up the scraping process (~ linear with the number of threads but please be kind to the server!)

Currently only captures data from the rankings (https://log.concept2.com/rankings). It does not record athlete logbook entries that are not ranked.

## Starting the Scraper
The default configuration options should be suitable for most systems. See [Configuration](#configuration) for available options.

If using the default configuration, you will need to create an "output" and a "cache" folder in the project root directory.

To run the scraper, run main.py using python.

## Configuration
The congiguration is a JSON file called "C2config.json", and should be in the root directory of the project. An example configuration is included in the repo. All are taken as strings unless otherwise specified.

The following options can be configured:

### max_ranking_tables
Integer. Specify the maximum number of ranking tables the program should visit. Useful for verifying the program will run to completion on your system before begining a long run. Normally can be left blank ("").

### use_cache
Boolean. Set to true to utilize cached files. This can significantly increase speed. See [caching][#caching]. If set to false, the scraper will neither read nor write cache files.

### threads
Integer. Specifify the maximum number of worker threads to use. See [Multi-Threading](#multi-threading). Set this to 0 if both (get_profile_data)[#get_profile_data] and (get_extended_workout_data)[#get_extended_workout_data] are set to false.

### Output File Paths
workouts_file/athletes_file/extended_file/athletes_cache_file/extended_cache_file.

Specify the path of the output files. See [Output](#output).

### url_profile_base
The root URL of the an athlete profile on the Concept2 logbook. This will usually not need changed.

### url_login
The URL of the Concept2 logbook login page. This will usually not need changed.

### C2_login
Boolean. Set to true to login to the website before scraping. Many athlete profiles are only visible to logged in users.

### C2_username
Username for logging in to the Concept2 logbook.

### C2_password
Password for logging in to the Concept2 logbook.

### write_buffer
Integer (seconds). The length of time between writing output files. The main process must suspend threads while writing output which takes a few seconds as the files grow in size. The main process checks the elapsed time between writing output files at the end of processing each ranking page. Recomended setting is 60 seconds or greater.

### get_profile_data
Scrape data from athlete profiles that the program finds while visiting the ranking tables. This requires an extra URL request per profile but this can be mitigated across multiple ranking tables by using [caching](#caching]. See [Output](#output).

### get_extended_workout_data
Scrape additional data about the workout by visiting the workout link on the ranking page. This requires an extra URL request per workout. See [Output](#output).

### machine_parameters
These settings determine which events, types of machine, weight class, gender and adaptive categories will be visited. The program will visit all combinations of ranking tables for the given options. Can be different for each type of machine (row, bike and ski erg). The default congiguration contains every option.

#### query parameters
List of strings. Exactly 4 parameters are required for each machine but they can be empty. For example, "rower" and "weight" are only used for the row erg.

#### events
List of integers. At least one should be present.

### url_parameters
#### url_base
The root URL of the Concept2 Logbook rankings.

#### url_years
List of integers. The year(s) of ranking boards that will be scraped.

## Multi-Threading
The scraper uses multi-threading, provided by the threading module, to speed up the scraping process. The scraper is rate limited by the speed at which it recieved its URL requests.

Multi-threading is optimised for scraping athlete profiles and extended workout profiles. The master process visits each ranking table page in turn, and adds each athlete profile and extended workout profile to a work queue. The worker threads then visit these URLs in turn and scrape the data.

As this scraper is not I/O or processer limited, you can have more threads than CPU cores and still experience a speed up.

The more worker threads present, the more load is put on the Concept2 Logbook server, please consider this when setting the number of threads. This developer's experience is that a URL request to the logbook takes about 1 second.

If scraping for athlete profile and extended workout profiles is disabled, the scraper will not be spead up with additional threads.

## Output
The scraper produces up to 5 output files.
### Workouts

### Extended Workout Profiles

### Athlete Profiles

### Extended Workout Profile Cache

### Athlete Profile Cache

## Cleaning and Analysis
TODO

## Caching
The scraper uses caching to minimize the number of URL requests to speed up the scraping process. With caching enabled the scraper will not make additional URL requests for athlete profiles or extended workout profiles that have been cached. This is particular effective when scraping multiple ranking boards and scraping athlete profile data as athletes are present on multiple boards.

##
