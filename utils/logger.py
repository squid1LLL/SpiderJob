#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
��־����ģ�飬�ṩͳһ����־��¼����
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import colorlog
import sys
from datetime import datetime

# ��־��ɫ����
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
        ��ʼ����־��¼��
        
        Args:
            log_name: ��־����
        """
        # ������־Ŀ¼
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # ��־�ļ�·��
        log_file = os.path.join(log_dir, f'{log_name}_{datetime.now().strftime("%Y%m%d")}.log')
        
        # ������־��¼��
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG)
        
        # �����ظ���Ӵ�����
        if not self.logger.handlers:
            # ����̨������������ɫ��
            console_handler = colorlog.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = colorlog.ColoredFormatter(
                fmt='%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors=log_colors_config
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # �ļ�������
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
        """��¼������־"""
        self.logger.debug(message)
    
    def info(self, message):
        """��¼��Ϣ��־"""
        self.logger.info(message)
    
    def warning(self, message):
        """��¼������־"""
        self.logger.warning(message)
    
    def error(self, message):
        """��¼������־"""
        self.logger.error(message)
    
    def critical(self, message):
        """��¼���ش�����־"""
        self.logger.critical(message)

# ����ȫ����־ʵ��
logger = Logger().logger
