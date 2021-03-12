# Concept2 Logbook Scraper

Scrapes the Concept2 Logbook site (log.concept2.com) and saves the information in JSON format. Uses multi-threading to spead up the scraping process (~ linear with the number of threads but please be kind to the server!)

Currently only captures information from the rankings (https://log.concept2.com/rankings).

## Config

### Query Parameters
Exactly 4 parameters must be present. If a query parameter has no values in the list, the list must be populated with "".
If you want to omit a query parameter (for example, if you do not want to filter by an adaptive category), use an empty ("") entry in the list