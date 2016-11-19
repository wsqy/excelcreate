import sys

# sys.path.append("/home/qy/excelcreate")
import logging.config
import logConfig
logging.config.dictConfig(logConfig.LOGGING)
loggerinfo = logging.getLogger("info")
loggererror = logging.getLogger("warning")

if __name__ == '__main__':
    loggererror.error("cuowu")
    loggerinfo.info("info")
