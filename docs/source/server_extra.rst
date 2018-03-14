.. include:: global.rst

Optional - Server Customisation
===============================
On this page we detail some of the server configurations you may want to change from standard.

Creating an SSH-Key
-------------------
To create an ssh key open command prompt on your local machine and:

1. ```ssh-keygen -t rsa -b 4096 -C "your_email@example.com"``
2. When asked where to save it, just use the default by hitting enter.
3. Next you will be asked to enter a passphrase, again just hit "enter". 
4. Check the files have been created:

    * On Mac: Run ```ls ~/.ssh```
    * On Windows: Run ```dir /c/Users/<YOUR_USERNAME>/```
    * On Linux: Run ```ls ~/.ssh```

You should see two the following files "id_rsa"  "id_rsa.pub" among others. Important! "id_rsa" is private, do NOT copy this anywhwere! The "id_rsa.pub" file is one you transfer to other machines.

5. Set the PUBLIC_SSH_KEY variable in the settings file to "~/.ssh/id_rsa.pub" for Mac and Linux users and "/c/Users/<YOUR_USERNAME>/" for Windows.

If you have not run the initial intall on the Pi yet then stop here. The SSH key will be added when the install begins. If you have already initialised the PI then run the following command: ```fab add_ssh_key -H littlesense.local```



Changing the .local Address
---------------------------
If you have used the NOOBs installation of Raspbian then you can find the Raspberry Pi using http://raspberrypi.local/ rather than entering the IP Address. This is nice, but maybe you want something more related with your project. To change the host name i.e. raspberrypi, do the following:

Using raspi-config
^^^^^^^^^^^^^^^^^^
1. Run ```sudo raspi-config```
2. Select "Network Options"
3. Select "Hostname"
4. Read the instructions and hit ok
5. Enter a new hostname.

Command line
^^^^^^^^^^^^
1. Connect to the Pi over SSH
2. Run ```sudo nano /etc/hosts``` 
3. Change the "raspberrypi" part of the last entry (```127.0.1.1 raspberrypi```) to the name of your choice. Make sure you conform to URL conventions; don't use spaces, etc.
4. Run ```sudo nano /etc/nginx/sites-enabled/<ROOT_NAME>``` where ROOT_NAME is the ROOT_NAME you specified in the settings file.
5. Change any occurances of "raspberrypi" to the new name. Save and exit.
6. Run ```sudo /etc/init.d/hostname.sh``` to update the PI
7. Run ```shutdown -r now``` to reboot the Pi.
8. Test your <new_name>.local in the browser once the Pi has rebooted. 

Reduce GPU memory
-----------------
If you have no intention of using the Raspberry Pi's desktop environment then you can reduce the amount of memory allocated to the GPU. This frees up memory for other applications and may improve preformance.

1. Run ```sudo raspi-config```
2. Select Advanced
3. Select TODO