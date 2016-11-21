#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import confWrap
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
conf = confWrap.CONF()


def mkdir_log_path(log_dir):
    if not os.path.isdir(log_dir):
        print("创建%s目录" % log_dir)
        os.makedirs(log_dir)


# 日志配置文件
def logging_file_path(log_type):
    log_path = conf.get("default", "log_dir")
    log_path = os.path.join(BASE_DIR, log_path)
    mkdir_log_path(log_path)
    return os.path.join(log_path, "%s.log" % log_type)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'notes': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logging_file_path('all'),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 5,
            'formatter': 'default',
        },
        'warning': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logging_file_path('warning'),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 5,
            'formatter': 'default',
        },
        'errors': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logging_file_path('error'),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 5,
            'formatter': 'default',
        },
    },
    'loggers': {
        'loggers': {
            'level': 'DEBUG',
            'handlers': ['console', 'notes', 'warning', 'errors'],
            'propagate': True
        }
    }

if __name__ == '__main__':
    logging_file_path("error")
