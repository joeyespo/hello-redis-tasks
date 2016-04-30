Hello Redis Tasks
=================

An example of how to use Redis as a task queue within a Flask web application.


Usage
-----

Be sure to have `redis-server` running.

When running locally, all you need to do is run `hello_redis_tasks.py` and it will use Flask to serve the
app and also to run background tasks. In production, you'll also have to run `worker.py` in a separate
process in addition to serving your app.


How It Works
------------

Clicking 'Add' will tell the web app to start a new task, then display the progress page. In the code, you'll see
that starting a new task is as simple as pushing some data onto a [Redis](http://redis.io/) list. The app is then
free to complete the web request the external `worker.py` process does all the work. Meanwhile the processing
page, using AJAX, will poll the server until it responds with 'ready=true', to which it redirects you to the results page.


Was this helpful?
-----------------

If you have any suggestions to make it even simpler or more clear,
please feel free to [let me know](http://www.twitter.com/joeyespo).

Also, if you find this useful, please consider supporting me on
<a href="http://gittip.com/joeyespo" title="Thank you!">
  <img align="center" style="margin-bottom:1px" src="http://joeyespo.com/images/gittip-button.png" alt="Gittip">
</a>
