#!/usr/bin/env python2.7
# coding:utf-8

from __future__ import print_function
import os
import sys

try:
    import configparser
except:
    # ConfigParser 2.x
    import ConfigParser as configparser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class CONF(object):
    """
    封装configparser主要是因为2与3中存在大小写问题
    和解析配置文件在本地和生产环境上的差异
    """
    def __init__(self):
        self.config_file = self.generateConFileName()
        self.conf = configparser.ConfigParser()
        self.conf.read(self.config_file)

    @staticmethod
    def generateConFileName():
        if os.path.isfile(os.path.join(BASE_DIR, "settings-public.ini")):
            return os.path.join(BASE_DIR, "settings-public.ini")
        else:
            return os.path.join(BASE_DIR, "settings.ini")

    def sections(self):
        return self.conf.sections()

    def options(self, key):
        return self.conf.options(key)

    def items(self, key):
        return self.conf.items(key)

    def get(self, key, name):
        return self.conf.get(key, name).strip()

    def getint(self, key, name):
        return self.con.getint(key, name)

    def getfloat(self, key, name):
        return self.con.getfloat(key, name)

    def getboolean(self, key, name):
        return self.con.getboolean(key, name)

if __name__ == '__main__':
    conf = CONF()
    print(conf.get("redis_config", "task_storage_key"))
