#!/usr/bin/env python2.7
# coding:utf-8

from __future__ import print_function, division

import os
import sys
import time
import json
import logging.config

import xlwt

import confWrap
from RedisObj import RedisObj
import logConfig

reload(sys)
sys.setdefaultencoding('utf8')
conf = confWrap.CONF()
sys.path.append(confWrap.BASE_DIR)
logging.config.dictConfig(logConfig.LOGGING)
loggerdebug = logging.getLogger("debug")
loggerinfo = logging.getLogger("info")
loggererror = logging.getLogger("error")


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
            loggererror.error(e)
        else:
            dbfiled = cur.description
            results = cur.fetchall()  # 搜取所有结果
            return dbfiled, results

    def select_fileld(self, sql):
        try:
            cur = self._conn.cursor()
            cur.execute(sql)
        except Exception as e:
            loggererror.error(e)
        else:
            cur.scroll(0, mode='absolute')  # 重置游标的位置 从0开始
            result = cur.fetchone()  # 搜取结果
            return result

    def __del__(self):
        self._conn.close()


class Repote:
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
            self._vaule = RedisObj().get_task(self._report_key)
        except redis.exceptions.ConnectionError:
            self._vaule = None
            loggererror.error("redis连接失败,请检查配置文件")
        except Exception as e:
            self._vaule = None
            loggererror.error("redis连接失败:%s" % e)
        if not self._vaule:
            return
        self._uid = self._vaule.get("uid")
        self._action = self._vaule.get("action")
        self._sql = self._vaule.get("sql")
        self._time = self._vaule.get("time")

    @ staticmethod
    def handle_excelfiled(filed):
        if filed in mapfiledname:
            return mapfiledname.get(filed)
        else:
            return filed

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
            loggerinfo.info("创建文件夹:%s" % current_dir)

    def generateFileName(self):
        random_chr = conf.get("default", "random_chr")
        random_len = conf.getint("default", "random_chr_len")
        ranstr = "".join(random.sample(random_chr, random_len)).replace(" ", "")
        return "%s_%s_%s_%s_%s.xls.tmp" % (self._action, self._uid, timestr, random.randint(1000000, 9999999), ranstr)

    def create_excel(self, sql_filed, db_results):
        timestr = time.strftime('%Y%m%d', time.localtime(time.time()))
        current_dir = os.path.join(conf.get("default", "Report_Basedir"), timestr)
        self.create_report_path(timestr)
        # 生成报表的临时文件名
        current_filename = self.generateFileName()
        try:
            workbook = xlwt.Workbook()
            # 如果是pay.list那么表格名就是 table_pay
            # cell_overwrite_ok=True是为了允许修改单元格的
            workbook_sheet = workbook.add_sheet('table_' + self._action.split(".")[0], cell_overwrite_ok=True)
        except Exception as e:
            loggererror.error("创建报表失败: %s" % e)
        else:
            loggerinfo.info("开始创建一个报表: %s" % current_filename)
            number = 0
            for filed_number in range(0, len(sql_filed)):
                table_name = sql_filed[filed_number][0]
                if table_name in self.mapfiledname:
                    # 写入字段名  中文要保存到xls中必须 使用unicode来解，直接存会报错
                    workbook_sheet.write(0, number, unicode(self.mapfiledname.get(table_name)))
                    number += 1

            tmp_base_filename = os.path.join(current_dir, current_filename)
            workbook.save(tmp_base_filename)
            # 获取并写入数据段信息
            esql = ExecuteSQl()
            for row in range(0, len(db_results)):
                colnumber = 0
                for col in range(0, len(sql_filed)):
                    #   如果当前列不需要过滤
                    if self.is_filedfilter(sql_filed[col][0]) is False:
                        vaules = self.handle_excelvalue(esql, sql_filed[col][0], db_results[row][col])
                        workbook_sheet.write(row + 1, colnumber, u'%s' % vaules)
                        workbook.save(tmp_base_filename)
                        colnumber += 1

            # tmp_base_filename = os.path.join(current_dir, current_filename)
            workbook.save(tmp_base_filename)
            real_filename = os.path.splitext(current_filename)[0]
            real_base_filename = os.path.join(current_dir, real_filename)
            logger.info("报表路径为:%s" % real_base_filename)
            os.rename(tmp_base_filename, real_base_filename)
            return os.path.join(timestr, real_filename)

    def pay_list(self):
        loggerinfo.info("为%s生成报表" % self._uid)
        dbfiled, results = ExecuteSQl().select_sql(self._sql)
        loggerinfo.info("%s的报表数据取出完成" % self._uid)
        excelFile = self.create_excel(dbfiled, results)
        loggerinfo.info("%s的报表生成完成" % self._uid)

    def register_list(self):
        pass

    def other_list(self):
        pass

    def create_report(self):
        self.get_task()
        if not self._vaule:
            return
        loggerinfo.info("准备执行任务%s" % self._value)
        data = self._operator.get(self._action)()
