# coding:utf-8
import sys
sys.path.append("/home/qy/excelcreate")

import redis

redis_handler = redis.ConnectionPool(host="192.168.9.20", port=9979, db=0)
redis_con = redis.Redis(connection_pool=redis_handler)
try:
    print(redis_con.rpop("6yam:task:make-report"))
except redis.exceptions.ConnectionError as e:
    print("redis连接失败,请检查配置文件")
except Exception as e:
    print("2222")
