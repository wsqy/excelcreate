#!/usr/bin/env python2.7
# coding:utf-8

from __future__ import print_function
import os
import time
import json
import redis
import confWrap
conf = confWrap.CONF()


class RedisObj:
    def __init__(self):
        self.__redis_host = conf.get("redis_config", "host")
        self.__redis_port = conf.getint("redis_config", "port")
        self.__redis_db = conf.getint("redis_config", "db")
        self.__redis_password = conf.get("redis_config", "password")
        self.redis_sleep_time = conf.getint("default", "SLEEP_TIME")
        self.__redis_con = redis.Redis(connection_pool=self.get_redis_pool())

    def get_redis_pool(self):
        redis_handler = redis.ConnectionPool(host=self.__redis_host,
                                             port=self.__redis_port,
                                             db=self.__redis_db,
                                             password=self.__redis_password
                                             )

        return redis_handler

    def get_task(self, key):
        task_info = self.__redis_con.rpop(key)
        while not task_info:
            print("暂时无任务")
            time.sleep(self.redis_sleep_time)
            task_info = self.__redis_con.rpop(key)
        task_info = json.loads(task_info)
        return task_info

    def push_task(self, key, data, reverse=False):
        data = json.dumps(data)
        if reverse:
            self.__redis_con.rpush(key, data)
        else:
            self.__redis_con.lpush(key, data)

    def delete_task(self, key, data):
        data = json.dumps(data)
        self.__redis_con.lrem(key, data, 1)

    def get_task_count(self, key):
        return self.__redis_con.llen(key)

    def add_set(self, key, data):
        data = json.dumps(data)
        return self.__redis_con.sadd(key, data)

    def rem_set(self, key, data):
        data = json.dumps(data)
        return self.__redis_con.srem(key, data)

    def del_key(self, key):
        self.__redis_con.delete(key)

    def random_member(self, key):
        task_info = self.__redis_con.srandmember(key)
        task_info = json.loads(task_info)
        return task_info

    # 以下是有序集合的操作
    def get_earliest_ztask(self, key):
        task_info = self.__redis_con.zrangebyscore(key, '-inf', '+inf', 0, 1)[0]
        task_info = json.loads(task_info)
        return task_info

    def get_earliest_ztask_score(self, key, vaule):
        data = json.dumps(vaule)
        task_info = self.__redis_con.zscore(key, data)
        return task_info

    def remove_earliest_ztask(self, key, vaule):
        data = json.dumps(vaule)
        self.__redis_con.zrem(key, data)

    def add_zset(self, key, vaule, score):
        self.__redis_con.zadd(key, vaule, score)

    # 下面是string类型的操作
