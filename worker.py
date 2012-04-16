#!/usr/bin/env python
"""\
Worker
Provides classes and a decorator for using Redis as a task queue.
Run this script or start a TaskWorker instance to run background tasks.

Initial code can be found here: http://flask.pocoo.org/snippets/73/
"""

import logging
from threading import Thread
from pickle import dumps, loads
from uuid import uuid4
from redis import Redis, ConnectionError
from time import sleep
from traceback import format_exc
from flask import current_app


logger = logging.getLogger('worker')
redis = Redis()


class TaskWorker(Thread):
    """A dedicated task worker that runs on a separate thread."""
    def __init__(self, app=None, port=None, queue_key=None, rv_ttl=None, redis=None, worker_name=None, thread_name=None, debug=None):
        Thread.__init__(self, name=thread_name)
        self.daemon = True
        self.queue_key = queue_key
        self.port = port
        self.rv_ttl = rv_ttl or 500
        self.redis = redis or Redis()
        self.worker_name = worker_name or (thread_name if worker_name is None else None)
        self.debug = app.debug if (debug is None and app) else (debug or False)
        self._worker_prefix = (self.worker_name + ': ') if self.worker_name else ''
        # Try getting the queue key from the specified or current Flask application
        if not self.queue_key:
            if not app and not current_app:
                raise ValueError('Cannot connect to Redis since both queue_key and app were not provided and current_app is None.')
            self.queue_key = (app or current_app).config.get('REDIS_QUEUE_KEY', None)
            if not self.queue_key:
                raise ValueError('Cannot connect to Redis since REDIS_QUEUE_KEY was not provided in the application config.')
        # Connect to Redis for the first time so that connection exceptions happen in the caller thread
        if not self.debug:
            self.redis.ping()
    
    def reset(self):
        """Resets the database to an empty task queue."""
        try:
            redis.flushdb()
        except ConnectionError:
            pass
    
    def run(self):
        """Runs all current and future tasks."""
        logger.info(' * %sRunning task worker ("%s")', self._worker_prefix, self.queue_key)
        while True:
            try:
                self.run_task()
            except ConnectionError:
                logger.error(' * %sDisconnected, waiting for task queue...', self._worker_prefix)
                while True:
                    try:
                        redis.ping()
                        sleep(1)
                        break
                    except ConnectionError:
                        pass
                logger.info(' * %sConnected to task queue', self._worker_prefix)
            except Exception, ex:
                logger.error(self._worker_prefix + format_exc(ex))
    
    def run_task(self):
        """Runs a single task."""
        msg = self.redis.blpop(self.queue_key)
        func, task_id, args, kwargs = loads(msg[1])
        logger.info('%sStarted task: %s(%s%s)', self._worker_prefix, str(func.__name__), repr(args)[1:-1], ('**' + repr(kwargs) if kwargs else ''))
        try:
            rv = func(*args, **kwargs)
        except Exception, ex:
            rv = ex
        logger.info('%s-> Completed: %s', self._worker_prefix, repr(rv))
        if rv is not None:
            self.redis.set(task_id, dumps(rv))
            self.redis.expire(task_id, self.rv_ttl)


class Task(object):
    """Represents an intermediate result."""
    def __init__(self, task_id):
        object.__init__(self)
        self.id = task_id
        self._value = None
    
    @property
    def return_value(self):
        if self._value is None:
            rv_encoded = redis.get(self.id)
            if rv_encoded:
                self._value = loads(rv_encoded)
        return self._value
    
    @property
    def exists(self):
        return self._value or redis.exists(self.id)
    
    def delete(self):
        redis.delete(self.id)


def delayable(f):
    """Marks a function as delayable by giving it the 'delay' and 'get_task' members."""
    def delay(*args, **kwargs):
        queue_key = current_app.config['REDIS_QUEUE_KEY']
        task_id = '%s:result:%s' % (queue_key, str(uuid4()))
        s = dumps((f, task_id, args, kwargs))
        redis.set(task_id, '')
        redis.rpush(current_app.config['REDIS_QUEUE_KEY'], s)
        return Task(task_id)
    def get_task(task_id):
        result = Task(task_id)
        return result if result.exists else None
    f.delay = delay
    f.get_task = get_task
    return f


# Run dedicated task worker
if __name__ == '__main__':
    import sys
    
    # Get queue key from app config
    from hello_redis_tasks import app
    queue_key = app.config['REDIS_QUEUE_KEY']
    
    # It's easy to have multiple task worker instances
    task_workers = []
    try:
        for i in range(5):
            task_workers.append(TaskWorker(queue_key=queue_key, worker_name="Worker %d" % i))
            task_workers.start()
    except ConnectionError:
        logger.error('Could not connect to Redis. Be sure Redis is running before starting the worker.')
        sys.exit(1)
    
    # Wait forever, so we can receive KeyboardInterrupt to exit
    while any(filter(lambda w: w.is_alive(), task_workers)):
        sleep(1)
    logger.info(' * Task worker stopped')
