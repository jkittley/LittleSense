.. include:: global.rst

Common Issues
=============
In this section we make not of a few things which may trip you up when trying to connect devices to |project|.

Are you trying to connect to a .local address?
----------------------------------------------
Some devices and software libraries cannot automatically discover .local addresses. Instead try the IP address of the |project| server. You may also need to check that the Nginx configuration of your |project| server allows the IP address (see below).

Getting a 444 response?
-----------------------
Check that the Nginx configuration allows the IP address. Loging to the |project| server via SSH and type ```sudo nano /etc/nginx/sites-available/littlesense```. Make sure the IP address is listed as below.

.. code::

    # Block all names not in list i.e. prevent HTTP_HOST errors
    if ($host !~* ^(192.168.1.100|littlesense.local)$) {{
        return 444;
    }}

        
