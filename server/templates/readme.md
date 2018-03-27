# Little Sense
All bespoke HTML, CSS and Javascript is contained within these documents. Imported libraries and images are held in the 'static' folder. We specifically chose to defy convention and have the CSS and JS in the HTML to make it as clear as possible what code effects what. For more information see http://littlesense.readthedocs.io.

## How to query the server for data
To request data from the server you must post a JSON encoded list of device_id, variable name and aggregation function (e.g. max, mean) along with a start time, end time and interval period. The system will automatically aggregat the results, returning aggregated values for each variable for each interval in the specified time period. 
