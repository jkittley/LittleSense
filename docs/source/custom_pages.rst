.. include:: global.rst

Add new pages
=============
Should you want to add a new page to the site you can create a new template in the 'tempaltes' folder. The web interface is build on [Flask](http://flask.pocoo.org/) and the internet is full of great tutorials on how to build [Flask](http://flask.pocoo.org/) websites, so rather than repeat others, we point you to [Flask](http://flask.pocoo.org/) as a starting point. 

Querying readings from pages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Firstly we recommend adding dashboards rather than new pages. However if you need query the readings for some readon. Here is an example of how to do it. Details of what each field means can be found in the RESTfull API section.

.. code::

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


