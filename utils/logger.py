#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块，提供统一的日志记录功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import colorlog
import sys
from datetime import datetime

# 日志颜色配置
log_colors_config = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}

class Logger:
    def __init__(self, log_name='recruitment_crawler'):
        """
        初始化日志记录器
        
        Args:
            log_name: 日志名称
        """
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 日志文件路径
        log_file = os.path.join(log_dir, f'{log_name}_{datetime.now().strftime("%Y%m%d")}.log')
        
        # 创建日志记录器
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 控制台处理器（带颜色）
            console_handler = colorlog.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = colorlog.ColoredFormatter(
                fmt='%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors=log_colors_config
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # 文件处理器
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                fmt='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        """记录调试日志"""
        self.logger.debug(message)
    
    def info(self, message):
        """记录信息日志"""
        self.logger.info(message)
    
    def warning(self, message):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message):
        """记录错误日志"""
        self.logger.error(message)
    
    def critical(self, message):
        """记录严重错误日志"""
        self.logger.critical(message)

# 创建全局日志实例
logger = Logger().logger
