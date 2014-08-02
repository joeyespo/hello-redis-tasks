from hello_redis_tasks import app as application


from worker import TaskWorker
worker = TaskWorker(application, debug=application.debug)
worker.reset()
worker.start()
