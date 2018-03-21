.. include:: global.rst

Change the look and feel
========================
Making |project| your own couldn't be easier. There are a few things you need to know before you get started.

1. ```static/img/``` holds all the images.
2. ```templates/``` is where all the HTML, CSS and Javascript lives. The CSS and Javascript needed by each is either included in the template itself or in its parent. For experienced programmers this may appear as we have gone mad, but we chose to structure things this was so it is really obvious to novices what effects what.
3. ```templates/base.html``` is extended by all other templates. For more information about how to manipulate the templates see http://flask.pocoo.org/docs/templating/.



