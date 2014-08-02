import os
import sys
from traceback import format_exc


def log(message):
    __directory__ = os.path.dirname(__file__)
    logfile = os.path.join(__directory__, 'passenger.log')
    with open(logfile, 'a') as log:
        print >>log, message
        log.flush()


def create_application():
    # Adjust path
    sys.path.append(os.path.dirname(__file__))

    # Import app
    try:
        from hello_redis_tasks import app
    except Exception:
        log('Could not load app:\n' + str(format_exc()))
        return None

    # Run worker
    try:
        from worker import TaskWorker
        worker = TaskWorker(app, debug=app.debug)
        worker.reset()
        worker.start()
    except Exception:
        log('Could not load worker:\n' + str(format_exc()))
        return None

    # Handle request
    def application(environ, start_response):
        log('Application called')
        try:
            results = app(environ, start_response)
        except Exception:
            log('*** ERROR ***\n' + str(format_exc()) + '\n*************')
        return results

    return application


def create_error_application():
    def application(environ, start_response):
        start_response('200 OK', [('Content-type', 'text/plain')])
        return ['500 Internal Error']
    return application


# Init logs
log('Running ' + str(sys.executable))


# Check interpreter
INTERP = "/home/joeyespo/local/Python-2.7/bin/python"
if sys.executable != INTERP:
    try:
        log('Detected wrong interpreter location, swapping to, ' + INTERP)
        os.execl(INTERP, INTERP, *sys.argv)
        # Should resume execution from the top of the file
    except:
        log('Could not switch interpreters:\n' + str(format_exc()))


application = create_application() or create_error_application()
