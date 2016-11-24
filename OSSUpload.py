#!/bin/env python2.7
# coding:utf-8

import os
import time
import oss2

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


class OSSUpload(BaseUpload):
    def __init__(self, oss_config):
        self.__access_id = oss_config.get("ACCESS_ID")
        self.__access_key = oss_config.get("ACCESS_KEY")
        self.__endpoint = oss_config.get("ENDPOINT")
        self.__bucket = oss_config.get("BUCKET")

    def __connect_oss(self):
        auth = oss2.Auth(self.__access_id, self.__access_key)
        bucket = oss2.Bucket(auth, 'http://%s' % self.__endpoint, self.__bucket)
        return bucket

    def upload_file(self, cloud_file, file_to_upload):
        file_size = os.path.getsize(file_to_upload)
        if file_size > self.__file_critical_size:
            self.upload_chunk_file(cloud_file, file_to_upload)
            return
        bucket = self.__connect_oss()
        logger.info("开始上传%s到OSS中" % file_to_upload)
        startTime = time.time()
        bucket.put_object_from_file(cloud_file, file_to_upload)
        endTime = time.time()
        spendTime = endTime - startTime
        logger.info("Upload file %s spent %f second." % (file_to_upload, spendTime))
