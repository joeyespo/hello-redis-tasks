# Local config file

PORT = 80
SECRET_KEY = 'DEVELOPMENT-KEY'
REDIS_QUEUE_KEY = 'hello-redis-tasks'


# Logging defaults
LOGGING = {
    'version': 1,
    'handlers': { 'console': { 'level': 'DEBUG', 'class': 'logging.StreamHandler', } },
    'loggers': { 'worker': { 'handlers': ['console'], 'level': 'DEBUG', } }
}
