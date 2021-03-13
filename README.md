# Concept2 Logbook Scraper

Scrapes the Concept2 Logbook site (log.concept2.com) and saves the information in JSON format. Uses multi-threading to spead up the scraping process (~ linear with the number of threads but please be kind to the server!)

Currently only captures information from the rankings (https://log.concept2.com/rankings).

## Starting the Scraper
TODO

## Config
The congiguration is a JSON file called "C2config.json", and should be in the root directory of the project. An example configuration is included in the repo. The following options can be configured:

### workouts_file/athletes_file/extended_file/athletes_cache_file/extended_cache_file
Specify the path of the output files. See [Output](output) for more information on the output files.

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
