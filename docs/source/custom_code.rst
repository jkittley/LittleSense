.. include:: global.rst

Notes on editing CSS and JS
===========================
When you are looking at code someone else has written it can be very confusing and difficult to understand what impact the changes you make will have on other parts of the codebase whoch you may not have looked at yet. In |project|, all the Javascript and CSS is stored alongside the HTML in the template files. This means that when you want to make a change all the elements are available in one place and mor importantly, you can be sure that the changes you make only impact the template you are editing and the templates which extend it. 

In short, everything extends ```templates/base.html```. System templates all extend ```templates/system/base.html``` which extends ```templates/base.html``` but also includes ```templates/system/menu.html```.

Below is an inheritance diagram showing which templates extend what.

* base.html 
   * dashboards/index.html
   * system/base.html
      * backup.html
      * configure.html
      * db.html
      * devices.html
      * index.html
      * logs.html
      * preview.html
      * serial.html
      * ungerister.html

