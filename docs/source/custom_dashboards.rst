.. include:: global.rst

Dashboards
==========
Dashboards are just a collections of plots and can be defined in a Dashboard JSON files. These files can be found in the ```data/dashboards``` directory. |project| automatically scans this folder and adds new dashboards to the menu. Below we dicuss how dashboard files are constructed.

At the top level dashboards have 3 sections: A *header*, a *footer* and an array of *plots*. The header and footer can either be "null" as per the footer in the example below, or it can be an object with a title and text attribute, see header in example. 

.. code::

    {
        "header": {
            "title": "Some title",
            "text": "Some descriptive text"
        },
        "footer": null,
        "plots": [ "-- See below --" ]
    }

.. warning:: JSON does not like trailing commas (unlike Python) and is very strict! Curious Concept have a nice `validation tool <https://jsonformatter.curiousconcept.com/>`_ which will happlily point out all your mistakes.

Plots
-----
Each item in the plots array must be an object like the one in the example below.

.. code:: 

    "plots": [
        {
            "id": 1,
            "pos": 1,
            "title": "Plot 1",
            "width": 6,
            "help": "Some help text for the viewer",
            "metrics": [ '-- See below --' ],
            "time": {},
            "type": "timeseries",
            "refresh_interval_seconds": 5
        },
        ...
    ]

:id: Must be unique.
:pos: Used to order the plots. Starts in the top left.
:title: The plot title
:width: The plot width. A vaulue from 1 to 12
:help: Help text for the user
:metrics: See below
:time: See below
:type: The type of plot. Must be one of the following: "timeseries", more soon.
:refresh_interval_seconds: Number of seconds between each refresh of the plot. Can be set to null to disable automatic refresh.

Time
----
The time attribute must be an object and be structured as follows:

.. code:: 

    "time": {
        "start": null,
        "end": null,
        "reading_interval_seconds": 10,
        "period": {
            "days": 0,
            "hours": 0,
            "minutes": 5
        },
        "fill": "none"
    }

:start: The start of the time period to be displayed. If null the default will be the end minus the period.
:end: The end of the time period to be displayed. If null then the current time is used and will auto update to the current time each refresh. 
:reading_interval_seconds: Group readings into intervals of this many seconds.
:period: A period of time messured in days, hours and minutes. If start and end are set this is ignored. 
:fill: If "none" then reading_intervals which contain no readings will be skipped. If "null" then reading_intervals with no readings return a null value.

Metrics
-------
Metrics represent the data to be displayed and how to present it.

.. code::

    "metrics": [
        {
            "name": "Device 1: Signal (dB)",
            "field_id": "float_signal_db",
            "device_id": "test_device_1",
            "aggrfunc": "mean"             
        },
        ...
    ]

:name: A friendly name for the user to read
:field_id: The id of the field to be displayed
:device_id: The device from which the field should be obtained
:aggrfunc: The method of aggregating readings when grouped by intervals. The values should be set to one of the following depending on the data type of the field.

    - Numeric: 'count', 'mean', 'mode', 'median', 'sum', 'max', 'min', 'first' or 'last'. 
    - Booleans: 'count', 'first' or 'last' and 
    - Strings: 'count', 'first' or 'last'.

Full example
------------

.. code-block:: json

    {
        "header": null,
        "footer": null,
        "plots": [
            {
                "id": 1,
                "pos": 1,
                "title": "Plot 1",
                "width": 6,
                "help": "Some help text for the viewer",
                "metrics": [{
                    "name": "Device 1: Signal (dB)",
                    "field_id": "float_signal_db",
                    "device_id": "test_device_1",
                    "aggrfunc": "mean"             
                },{
                    "name": "Device 1: Max Light Level (Lux)",
                    "field_id": "int_light_level_lux",
                    "device_id": "test_device_1",
                    "aggrfunc": "max"
                },{
                    "name": "Device 2: Switch State (OnOff)",
                    "field_id": "bool_switch_state",
                    "device_id": "test_device_2",
                    "aggrfunc": "count"
                }],
                "time": {
                    "start": null,
                    "end": null,
                    "reading_interval_seconds": 10,
                    "period": {
                        "days": 0,
                        "hours": 0,
                        "minutes": 5
                    },
                    "fill": "none"
                },
                "type": "timeseries",
                "refresh_interval_seconds": 5
            },
            {
                "id": 2,
                "pos": 2,
                "title": "Plot 2",
                "width": 6,
                "help": "Some help text for the viewer",
                "metrics": [{
                    "name": "Device 2: Temp (C)",
                    "field_id": "float_temp_c",
                    "device_id": "test_device_2",
                    "agrfunc": "mean"             
                },{
                    "name": "Device 2: Switch State (OnOff)",
                    "field_id": "bool_switch_state",
                    "device_id": "test_device_2",
                    "aggrfunc": "count"
                }],
                "time": {
                    "start": null,
                    "end": null,
                    "reading_interval_seconds": 5,
                    "period": {
                        "days": 0,
                        "hours": 0,
                        "minutes": 5
                    },
                    "fill": "none"
                },
                "type": "timeseries",
                "refresh_interval_seconds": 5
            }
            ]
    }