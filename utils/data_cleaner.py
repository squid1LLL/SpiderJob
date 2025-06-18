#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import pandas as pd
from utils.logger import logger

class DataCleaner:
    """������ϴ�࣬������͹淶����ȡ������"""
    
    @staticmethod
    def clean_job_data(job_data):
        """
        ��ϴְλ����
        
        Args:
            job_data: ԭʼְλ�����б��б����ֵ䣩
            
        Returns:
            list: ��ϴ���ְλ�����б��ֵ��б�
        """
        if not job_data:
            logger.warning("û��������Ҫ��ϴ")
            return []
        
        cleaned_data = []
        for idx, job in enumerate(job_data):
            if not job:
                continue
            try:
                cleaned_job = {}
                
                # ְλ����
                cleaned_job["ְλ����"] = DataCleaner._clean_job_title(job.get("ְλ����", ""))
                
                # ��˾����
                cleaned_job["��˾����"] = DataCleaner._clean_company_name(job.get("��˾����", ""))
                
                # н��
                salary_raw = job.get("н��", "")
                cleaned_job["н��"] = DataCleaner._clean_salary(salary_raw)
                
                # ��ȡн�ʷ�Χ����λK��
                salary_range = DataCleaner._extract_salary_range(salary_raw)
                if salary_range:
                    cleaned_job["���н��(K)"] = salary_range[0]
                    cleaned_job["���н��(K)"] = salary_range[1]
                    cleaned_job["ƽ��н��(K)"] = (salary_range[0] + salary_range[1]) / 2
                else:
                    cleaned_job["���н��(K)"] = None
                    cleaned_job["���н��(K)"] = None
                    cleaned_job["ƽ��н��(K)"] = None
                
                # �����ص㣬ȥ���������е㣬ͳһΪ���ŷָ�
                location_raw = job.get("�����ص�", "")
                cleaned_job["�����ص�"] = DataCleaner._clean_location(location_raw)
                
                # ҳ��
                cleaned_job["ҳ��"] = job.get("ҳ��", None)
                
                cleaned_data.append(cleaned_job)
            except Exception as e:
                logger.error(f"��ϴ��{idx}�������쳣: {e}")
        
        logger.info(f"������ϴ��ɣ������� {len(cleaned_data)} ����¼")
        return cleaned_data
    
    @staticmethod
    def _clean_job_title(title):
        if not title:
            return ""
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    @staticmethod
    def _clean_company_name(name):
        if not name:
            return ""
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\u4e00-\u9fff\(\)\[\]\{\}\.\,\-]+', '', name)
        return name
    
    @staticmethod
    def _clean_salary(salary):
        if not salary:
            return ""
        salary = re.sub(r'\s+', ' ', salary).strip()
        return salary
    
    @staticmethod
    def _clean_location(location):
        if not location:
            return ""
        # ȥ�������ź������ַ����滻 �� �� �� Ϊ����
        loc = re.sub(r'[����\[\]]', '', location)
        loc = re.sub(r'[����]', ',', loc)
        loc = loc.strip()
        return loc
    
    @staticmethod
    def _extract_salary_range(salary_str):
        """
        ��н���ַ�������ȡн�ʷ�Χ����λͳһתΪK
        
        ֧�ָ�ʽʾ����
        - 6000-12000Ԫ��13н  -> תΪ6-12K
        - 1.1-1.3��         -> 11-13K
        - 150-200Ԫ/��      -> ����None����Ϊ��λ��ͬ���ݲ�����
        - ����              -> ����None
        
        Returns:
            tuple or None: (min_salary_k, max_salary_k)
        """
        if not salary_str:
            return None
        
        salary_str = salary_str.lower()
        
        # ����ǡ����顱�������֣�ֱ�ӷ���None
        if any(x in salary_str for x in ["����", "����", "����", "negotiable"]):
            return None
        
        # ��н��Сʱн������
        if re.search(r'[Ԫ��]/(��|Сʱ|ʱ)', salary_str):
            return None
        
        # ������н����Ԫ����λ��תΪǧԪ��λ
        match_yuan = re.match(r'(\d+)[-~](\d+)Ԫ', salary_str)
        if match_yuan:
            min_val = float(match_yuan.group(1)) / 1000
            max_val = float(match_yuan.group(2)) / 1000
            return (min_val, max_val)
        
        # ��������򡱵�λ����н���� 1.1-1.3��תΪ 11-13K
        match_wan = re.match(r'(\d+\.?\d*)[-~](\d+\.?\d*)��', salary_str)
        if match_wan:
            min_val = float(match_wan.group(1)) * 10
            max_val = float(match_wan.group(2)) * 10
            return (min_val, max_val)
        
        # �������k����ǧ������н���� 6k-12k �� 6K-12K
        match_k = re.match(r'(\d+\.?\d*)[kǧ]?[-~](\d+\.?\d*)[kǧ]?', salary_str)
        if match_k:
            min_val = float(match_k.group(1))
            max_val = float(match_k.group(2))
            return (min_val, max_val)
        
        return None
    
    @staticmethod
    def analyze_data(df):
        """
        ������ϴ������ݣ�����ͳ����Ϣ
        
        Args:
            df: pandas DataFrame
            
        Returns:
            dict: ͳ����Ϣ
        """
        stats = {}
        try:
            stats["��ְλ��"] = len(df)
            if "ƽ��н��(K)" in df.columns:
                stats["ƽ��н��(K)"] = round(df["ƽ��н��(K)"].dropna().mean(), 2)
                stats["���н��(K)"] = round(df["���н��(K)"].dropna().max(), 2)
                stats["���н��(K)"] = round(df["���н��(K)"].dropna().min(), 2)
            
            if "��˾����" in df.columns:
                stats["��˾����"] = df["��˾����"].nunique()
                stats["��Ƹְλ���Ĺ�˾"] = df["��˾����"].value_counts().head(5).to_dict()
            
            if "�����ص�" in df.columns:
                stats["ְλ���ĵ���"] = df["�����ص�"].value_counts().head(5).to_dict()
            
            logger.info("���ݷ������")
        except Exception as e:
            logger.error(f"���ݷ�������: {e}")
        return stats
