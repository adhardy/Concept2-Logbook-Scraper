# Concept2 Logbook Scraper

Scrapes the Concept2 Logbook site (log.concept2.com) and saves the information in JSON format. Uses multi-threading to spead up the scraping process (~ linear with the number of threads but please be kind to the server!)

Currently only captures information from the rankings (https://log.concept2.com/rankings).

## Starting the Scraper
TODO

## Config
The congiguration is a JSON file called "C2config.json", and should be in the root directory of the project. An example configuration is included in the repo. All are taken as strings unless otherwise specified.

The following options can be configured:

### max_ranking_tables
Integer. Specify the maximum number of ranking tables the program should visit. Useful for verifying the program will run to completion on your system before begining a long run. Normally can be left blank ("").

### use_cache
Boolean. Set to true to utilize cached files. This can significantly increase speed. See [caching][#caching].

### threads
Integer. Specifify the maximum number of worker threads to use. See [Multi-Threading](#multi-threading).

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
Integer (seconds). The length of time between writing output files. The main process must suspend threads while writing output which takes a few seconds as the files grow in size. Recomend setting this to 60 seconds.

### get_profile_data
Scrape data from athlete profiles that the program finds while visiting the ranking tables. This requires an extra URL request per profile but this can be mitigated across multiple ranking tables by using [caching](#caching]. See [Output](#output).

### get_extended_workout_data
Scrape additional data about the workout by visiting the workout link on the ranking page. This requires an extra URL request per workout. See [Output](#output).

### Query Parameters
Exactly 4 parameters must be present. If a query parameter has no values in the list, the list must be populated with "".
If you want to omit a query parameter (for example, if you do not want to filter by an adaptive category), use an empty ("") entry in the list

### max_ranking_tables

### use_cache

## Multi-Threading
TODO

## Output
TODO

## Cleaning and Analysis
TODO

## Caching

##
