#!/usr/bin/env python2.7
# coding:utf-8

from __future__ import print_function, division

import os
import sys
import time
import json
import random
import socket
import signal
import hashlib
import logging.config

import xlwt
import redis
# import gevent
import MySQLdb
# from gevent import monkey


import confWrap
from RedisObj import RedisObj
import logConfig

reload(sys)
sys.setdefaultencoding('utf8')
# monkey.patch_all()
conf = confWrap.CONF()
sys.path.append(confWrap.BASE_DIR)
logging.config.dictConfig(logConfig.LOGGING)
logger = logging.getLogger("loggers")


class ExecuteSQl(object):
    def __init__(self):
        self._host = conf.get("db_config", "host")
        self._db = conf.get("db_config", "db")
        self._user = conf.get("db_config", "user")
        self._passwd = conf.get("db_config", "passwd")
        self._charset = conf.get("db_config", "charset")
        self._pay_table = conf.get("db_config", "pay_table")
        self._conn = MySQLdb.connect(host=self._host,
                                     db=self._db,
                                     user=self._user,
                                     passwd=self._passwd,
                                     charset=self._charset
                                     )

    def select_sql(self, sql):
        try:
            cur = self._conn.cursor()
            cur.execute(sql)
        except Exception as e:
            logger.error(e)
        else:
            dbfiled = cur.description
            results = cur.fetchall()  # 搜取所有结果
            return dbfiled, results

    def select_fileld(self, sql):
        try:
            cur = self._conn.cursor()
            cur.execute(sql)
        except Exception as e:
            logger.error(e)
        else:
            cur.scroll(0, mode='absolute')  # 重置游标的位置 从0开始
            result = cur.fetchone()  # 搜取结果
            return result

    def __del__(self):
        self._conn.close()


class Repore:
    def __init__(self):
        self._report_key = conf.get("default", "task_storage_key")
        self._operator = {"pay.list": self.pay_list, "register.list": self.register_list, "other": self.other_list}
        self.mapfiledname = {'orderid': '订单号', 'amount': '支付金额', 'real_amount': '实际支付金额',
                             'real_ptb': '实际支付平台币', 'username': '用户名', 'serverid': '服务器id',
                             'game_name': '游戏名', 'status': '支付状态', 'create_time': '创建时间',
                             'channel_id': '顶级渠道', 'dep_name': '渠道名称', 'payname': '支付方式'
                             }

    def get_task(self):
        try:
            vaule = RedisObj().get_task(self._report_key)
        except redis.exceptions.ConnectionError:
            vaule = None
            logger.error("redis连接失败,请检查配置文件")
        except Exception as e:
            vaule = None
            logger.error("redis连接失败:%s" % e)
        finally:
            return vaule

    @staticmethod
    def handle_excelvalue(esql, filed, value):
        if filed == 'status':
            if value == 0:
                value = '未支付'
            elif value == 1:
                value = '支付'

        if filed == 'create_time':
            value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))

        if filed == 'channel_id':
            try:
                sql = "select id_path from cy_department where id = '%s'" % (str(value))
                dbresults = esql.select_fileld(sql)
                depid = u'%s' % dbresults

                if '35,' in depid:
                    topdep_id = depid.split(",")[depid.index('35') + 1]
                    sql = "select name from cy_department where id = '%s'" % str(topdep_id)
                    depname = esql.select_fileld(sql)
                    value = u'%s' % depname
                else:
                    value = '---'
            except Exception as e:
                value = '---'

        return value

    @staticmethod
    def create_report_path(current_dir):
        # 判断文件夹是否存在  无则创建
        if not os.path.exists(current_dir):
            os.makedirs(current_dir)
            logger.info("创建文件夹:%s" % current_dir)

    def generateFileName(self, vaule, timestr):
        random_chr = conf.get("default", "random_chr")
        random_len = conf.getint("default", "random_chr_len")
        ranstr = "".join(random.sample(random_chr, random_len)).replace(" ", "")
        return "%s_%s_%s_%s_%s.xls.tmp" % (vaule.get("action"), vaule.get("uid"), timestr, random.randint(1000000, 9999999), ranstr)

    def create_excel(self, vaule, sql_filed, db_results):
        real_base_filename = None
        timestr = time.strftime('%Y%m%d', time.localtime(time.time()))
        current_dir = os.path.join(conf.get("default", "Report_Basedir"), timestr)
        self.create_report_path(current_dir)
        # 生成报表的临时文件名
        current_filename = self.generateFileName(vaule, timestr)
        logger.info("准备生成")
        try:
            workbook = xlwt.Workbook()
            # 如果是pay.list那么表格名就是 table_pay
            # cell_overwrite_ok=True是为了允许修改单元格的
            workbook_sheet = workbook.add_sheet('table_' + vaule.get("action").split(".")[0], cell_overwrite_ok=True)
        except Exception as e:
            logger.error("创建报表失败: %s" % e)
        else:
            logger.info("开始创建一个报表: %s" % current_filename)
            number = 0
            for filed_number in range(0, len(sql_filed)):
                table_name = sql_filed[filed_number][0]
                if table_name in self.mapfiledname:
                    # 写入字段名  中文要保存到xls中必须 使用unicode来解，直接存会报错
                    workbook_sheet.write(0, number, unicode(self.mapfiledname.get(table_name)))
                    number += 1
            tmp_base_filename = os.path.join(current_dir, current_filename)
            logger.info(tmp_base_filename)
            workbook.save(tmp_base_filename)
            logger.info("开始进行报表数据填充(任务略微有点耗时,请耐心等待)....")
            # 获取并写入数据段信息
            esql = ExecuteSQl()
            for row in range(0, len(db_results)):
                colnumber = 0
                for col in range(0, len(sql_filed)):
                    try:
                        #   如果当前列不需要过滤
                        table_name = sql_filed[col][0]
                        if table_name in self.mapfiledname:
                            vaules = self.handle_excelvalue(esql, sql_filed[col][0], db_results[row][col])
                            workbook_sheet.write(row + 1, colnumber, u'%s' % vaules)
                            colnumber += 1

                    except Exception as e:
                        logger.error("当前数据异常")
            logger.info("报表数据填充完成")
            # tmp_base_filename = os.path.join(current_dir, current_filename)
            workbook.save(tmp_base_filename)
            real_filename = os.path.splitext(current_filename)[0]
            real_base_filename = os.path.join(current_dir, real_filename)
            logger.info("报表路径为:%s" % real_base_filename)
            os.rename(tmp_base_filename, real_base_filename)
        finally:
            return real_base_filename

    def pay_list(self, vaule):
        logger.info("为%s生成报表" % vaule.get("uid"))
        dbfiled, results = ExecuteSQl().select_sql(vaule.get("sql"))
        logger.info("%s的报表数据取出完成" % vaule.get("uid"))
        excelFile = self.create_excel(vaule, dbfiled, results)
        return excelFile

    def register_list(self, vaule):
        pass

    def other_list(self, vaule):
        pass

    def delete_uniqueId(self, vaule):
        unique_name = "%s|%s|%s" % (vaule.get("uid"), vaule.get("action"), vaule.get("sql"))
        unique_name_byte = unique_name.encode()
        md5_en = hashlib.md5()
        md5_en.update(unique_name_byte)
        unique_id = md5_en.hexdigest()
        task_unique_prefix = conf.get("default", "task_unique_prefix")
        task_unique = "%s:%s" % (task_unique_prefix, unique_id)
        logger.info(task_unique)
        try:
            RedisObj().del_key(task_unique)
            logger.warning("删除了redis key: %s" % task_unique)
        except Exception as e:
            logger.error("删除redis key: %s 失败：%s " % (task_unique, e))

    def notice(self, excelFile, vaule):
        ReportBasedir = conf.get("default", "Report_Basedir")
        relative_Path = excelFile[len(ReportBasedir) + 1:]
        logger.info(relative_Path)
        sendData = {
            "action": "saytouid",
            "data": {
                "uid": vaule.get("uid"),
                "action": "makeExcelComplete",
                "data": {
                    "file_path": relative_Path,
                    "task_time": vaule.get("time"),
                    "file_type": vaule.get("action"),
                }
            }
        }
        try:
            hConnect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            hConnect.connect((conf.get('socket', 'host'), conf.getint('socket', 'port')))
            hConnect.sendall(json.dumps(sendData))
            hConnect.close()
        except Exception as e:
            logger.error("通知失败:%s" % e)
        # TODO添加条件 什么时候删除
        if True:
            self.delete_uniqueId(vaule)

    def create_report(self):
        vaule = self.get_task()
        if not vaule:
            return
        logger.info("准备执行任务%s" % vaule)
        excelFile = self._operator.get(vaule.get("action"))(vaule)
        if not excelFile:
            logger.error("不能建立报表")
            return
        self.notice(excelFile, vaule)


def delete_excel():
    Report_Basedir = conf.get("default", "Report_Basedir")
    if not os.path.isdir(Report_Basedir):
        return
    DELETE_REPORT_TIME = conf.get("default", "DELETE_REPORT_TIME")

    for file in os.listdir(Report_Basedir):
        # 今天的文件夹跳过
        if time.strftime('%Y%m%d', time.localtime(time.time())) != os.path.basename(file):
            filePath = os.path.join(Report_Basedir, file)
            # 空文件夹删除
            if not os.listdir(filePath):
                logger.info("删除空文件夹%s" % filePath)
                os.rmdir(filePath)
            else:
                for f in os.listdir(filePath):
                    excelfile = os.path.join(filePath, f)
                    if time.time() - os.path.getctime(excelfile) > DELETE_REPORT_TIME:
                        logger.info("文件%s已到期，删除" % excelfile)
                        os.remove(excelfile)


class ControlEngine:
    """
    消息通知主程序
    """
    def __init__(self):
        self.__be_kill = False
        self.REPORT_THREADS_NUM = conf.getint("default", "REPORT_THREADS_NUM")

    def setQuit(self, pid, signal_num):
        logger.warning("kill by USR2")
        self.__be_kill = True

    def gevent_join(self):
        gevent_task = []
        for each in range(self.REPORT_THREADS_NUM):
            gevent_task.append(gevent.spawn(self.creatExcel))
        gevent_task.append(gevent.spawn(self.deleteExcel))
        logger.info("add gevent task suceess")
        gevent.joinall(gevent_task)

    def creatExcel(self):
        while not self.__be_kill:
            logger.info("excel task start")
            reporeTask = Repore()
            reporeTask.create_report()

    def deleteExcel(self):
        while not self.__be_kill:
            logger.info("del task start")
            try:
                delete_excel()
                sleep_time = conf.getint("default", "DELETE_SLEEP_TIME")
                time.sleep(int(sleep_time))
            except Exception as e:
                logger.error(e)


if __name__ == "__main__":
    # control_engine = ControlEngine()
    # logger.info('start task....')
    # signal.signal(signal.SIGUSR2, control_engine.setQuit)
    # control_engine.gevent_join()
    reporeTask = Repore()
    reporeTask.create_report()
