# coding:utf-8
import sys
sys.path.append("/home/qy/excelcreate")

import redis
import json

redis_handler = redis.ConnectionPool(host="192.168.5.10")
redis_con = redis.Redis(connection_pool=redis_handler)
# try:
#     print(redis_con.rpop("6yam:task:make-report"))
# except redis.exceptions.ConnectionError as e:
#     print("redis连接失败,请检查配置文件")
# except Exception as e:
#     print("2222")

data = {
    "action": "pay.list",
    "sql": " SELECT Pay.id AS pay_id,Pay.orderid AS orderid,Pay.userid AS userid,Pay.amount AS amount,Pay.real_amount AS real_amount,Pay.real_ptb AS real_ptb,Pay.username AS username,Pay.paytype AS paytype,Pay.serverid AS serverid,Pay.gameid AS gameid,Pay.status AS status,Pay.create_time AS create_time,Pay.channel_id AS channel_id,Game.name AS game_name,Department.name AS dep_name,Paytype.payname AS payname FROM cy_pay Pay LEFT JOIN cy_game Game ON Pay.gameid = Game.id LEFT JOIN cy_department Department ON Pay.channel_id = Department.id LEFT JOIN cy_paytype Paytype ON Pay.paytype = Paytype.paytype WHERE ( Pay.gameid = '409' ) ORDER BY Pay.id DESC  ",
    "uid": 1,
    "time": 1479717436
}

datas = json.dumps(data)
print(datas)
redis_con.rpush("6yam:task:make-report", datas)
