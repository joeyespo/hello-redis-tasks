#!/usr/bin/env python
"""\
Hello Redis Tasks
A quick example of how to use Redis as a task queue.
"""

import logging.config
import os
from redis import ConnectionError
from flask import Flask, render_template, request, redirect, jsonify
from tasks import add


# Flask application
app = Flask(__name__)
app.config['DEBUG'] = __name__ == '__main__'
app.config.from_pyfile('config.py')
if 'LOGGING' in app.config:
    logging.config.dictConfig(app.config['LOGGING'])


# Views
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add')
def add_start():
    """Grabs the args from the URL, starts the task, then redirects to show progress."""
    x = request.args.get('x', 2, type=int)
    y = request.args.get('y', 3, type=int)
    task = add.delay(x, y)
    return redirect('/progress?tid=' + task.id)


@app.route('/progress')
def add_progress():
    """Shows the progress of the current task or redirect home."""
    task_id = request.args.get('tid')
    return render_template('progress.html', task_id=task_id) if task_id else redirect('/')


@app.route('/poll')
def add_poll():
    """Called by the progress page using AJAX to check whether the task is complete."""
    task_id = request.args.get('tid')
    try:
        task = add.get_task(task_id)
    except ConnectionError:
        # Return the error message as an HTTP 500 error
        return 'Coult not connect to the task queue. Check to make sure that <strong>redis-server</strong> is running and try again.', 500
    ready = task.return_value is not None if task else None
    return jsonify(ready=ready)


@app.route('/results')
def add_results():
    """When poll_task indicates the task is done, the progress page redirects here using JavaScript."""
    task_id = request.args.get('tid')
    task = add.get_task(task_id)
    if not task:
        return redirect('/')
    result = task.return_value
    if not result:
        return redirect('/progress?tid=' + task_id)
    task.delete()
    # Redis can also be used to cache results
    return render_template('results.html', value=result)


# Errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message='Not Found', description='The requested URL was not found on the server.'), 404


@app.errorhandler(ConnectionError)
def connection_error(e):
    debug_description = "<strong>redis-server</strong> is"
    production_description = "both <strong>redis-server</strong> and <strong>worker.py</strong> are"
    description = "Check to make sure that %s running." % (debug_description if app.debug else production_description)
    return render_template('error.html', message='Coult not connect to the task queue', description=description), 500


# Run dev server
if __name__ == '__main__':
    # Run both the task queue
    # TODO: When Flask version 0.8, refactor using the new
    #       app.before_first_request()
    debug = app.config.get('DEBUG', True)
    use_reloader = app.config.get('DEBUG', True)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not use_reloader:
        from worker import TaskWorker
        worker = TaskWorker(app, debug=debug)
        worker.reset()
        worker.start()
    app.run(host=app.config.get('HOST'), port=app.config.get('PORT'),
            debug=debug, use_reloader=use_reloader)
