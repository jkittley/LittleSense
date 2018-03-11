# Sensor Store
All bespoke HTML, CSS and Javascript is contained withing these documents. Imported libraries and images are held in the 'static' folder. We specifically chose to defy convention and have the CSS and JS in the HTML to make it as clear as possible what code effects what.

## How to query the server for data
To request data from the server you must post a JSON encoded list of device_id, variable name and aggregation function (e.g. max, mean) along with a start time, end time and interval period. The system will automatically aggregat the results, returning aggregated values for each variable for each interval in the specified time period. 

```
$.ajax({
    dataType: "json",
    method: "POST",
    url: "/api/readings/get",
    data: {
        start: "2018-01-11T09:16:50+00:00",
        end: "2018-03-11T09:14:50+00:00",
        fill: "null",
        interval: reading_interval,
        metrics: JSON.stringify([{
                "name": "Device 10: Temp (C)",
                "field_id": "float_temp_c",
                "device_id": "test_device_10",
                "agrfunc": "mean"
            },{
                "name": "Device 10: Light Level (Lux)",
                "field_id": "int_light_level_lux",
                "device_id": "test_device_4",
                "agrfunc": "max"
            }]),
        success: function(results) {},
        error:  function(results) {}
}
```

The fill option determines what the server does when there are no results for an interval. null will return a result but with null values for the fields. The value 'none' will just skip the interval and not return any data for this slot.