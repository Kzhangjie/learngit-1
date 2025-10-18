import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime


def getLogger(name):
    # 创建一个日志记录器，并设置其日志级别为最低级别
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 必须至少为DEBUG，以便捕获所有消息

    # 创建一个根据时间自动分割日志的文件处理器，并设置日志级别为DEBUG
    # 日志文件名格式为：name-YYYY-MM-DD.log
    log_filename = f'./logs/{name}-{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = TimedRotatingFileHandler(
        log_filename, when="midnight", backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    # 设置TimedRotatingFileHandler以在午夜时分割日志文件，并保留1个备份文件（即今天和昨天的日志）

    # 创建一个控制台处理器，设置日志级别为INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    # 将文件处理器和控制台处理器添加到日志记录器
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)

    # 清理超过两天的日志文件
    for handler in logger.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            handler.namer = lambda name: name.replace(".log", "") + ".log"
            handler.rotator = os.rename

    return logger
