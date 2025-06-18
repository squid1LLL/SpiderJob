#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import pandas as pd
from utils.logger import logger

class DataCleaner:
    """数据清洗类，负责处理和规范化爬取的数据"""
    
    @staticmethod
    def clean_job_data(job_data):
        """
        清洗职位数据
        
        Args:
            job_data: 原始职位数据列表（列表内字典）
            
        Returns:
            list: 清洗后的职位数据列表（字典列表）
        """
        if not job_data:
            logger.warning("没有数据需要清洗")
            return []
        
        cleaned_data = []
        for idx, job in enumerate(job_data):
            if not job:
                continue
            try:
                cleaned_job = {}
                
                # 职位名称
                cleaned_job["职位名称"] = DataCleaner._clean_job_title(job.get("职位名称", ""))
                
                # 公司名称
                cleaned_job["公司名称"] = DataCleaner._clean_company_name(job.get("公司名称", ""))
                
                # 薪资
                salary_raw = job.get("薪资", "")
                cleaned_job["薪资"] = DataCleaner._clean_salary(salary_raw)
                
                # 提取薪资范围（单位K）
                salary_range = DataCleaner._extract_salary_range(salary_raw)
                if salary_range:
                    cleaned_job["最低薪资(K)"] = salary_range[0]
                    cleaned_job["最高薪资(K)"] = salary_range[1]
                    cleaned_job["平均薪资(K)"] = (salary_range[0] + salary_range[1]) / 2
                else:
                    cleaned_job["最低薪资(K)"] = None
                    cleaned_job["最高薪资(K)"] = None
                    cleaned_job["平均薪资(K)"] = None
                
                # 工作地点，去掉「」和中点，统一为逗号分隔
                location_raw = job.get("工作地点", "")
                cleaned_job["工作地点"] = DataCleaner._clean_location(location_raw)
                
                # 页码
                cleaned_job["页码"] = job.get("页码", None)
                
                cleaned_data.append(cleaned_job)
            except Exception as e:
                logger.error(f"清洗第{idx}条数据异常: {e}")
        
        logger.info(f"数据清洗完成，处理了 {len(cleaned_data)} 条记录")
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
        # 去除中括号和特殊字符，替换 · 或 、 为逗号
        loc = re.sub(r'[「」\[\]]', '', location)
        loc = re.sub(r'[·、]', ',', loc)
        loc = loc.strip()
        return loc
    
    @staticmethod
    def _extract_salary_range(salary_str):
        """
        从薪资字符串中提取薪资范围，单位统一转为K
        
        支持格式示例：
        - 6000-12000元·13薪  -> 转为6-12K
        - 1.1-1.3万         -> 11-13K
        - 150-200元/天      -> 返回None（因为单位不同，暂不处理）
        - 面议              -> 返回None
        
        Returns:
            tuple or None: (min_salary_k, max_salary_k)
        """
        if not salary_str:
            return None
        
        salary_str = salary_str.lower()
        
        # 如果是“面议”或无数字，直接返回None
        if any(x in salary_str for x in ["面议", "不限", "待定", "negotiable"]):
            return None
        
        # 日薪或小时薪不处理
        if re.search(r'[元块]/(天|小时|时)', salary_str):
            return None
        
        # 处理月薪带“元”单位，转为千元单位
        match_yuan = re.match(r'(\d+)[-~](\d+)元', salary_str)
        if match_yuan:
            min_val = float(match_yuan.group(1)) / 1000
            max_val = float(match_yuan.group(2)) / 1000
            return (min_val, max_val)
        
        # 处理带“万”单位的月薪，如 1.1-1.3万，转为 11-13K
        match_wan = re.match(r'(\d+\.?\d*)[-~](\d+\.?\d*)万', salary_str)
        if match_wan:
            min_val = float(match_wan.group(1)) * 10
            max_val = float(match_wan.group(2)) * 10
            return (min_val, max_val)
        
        # 处理带“k”或“千”的月薪，如 6k-12k 或 6K-12K
        match_k = re.match(r'(\d+\.?\d*)[k千]?[-~](\d+\.?\d*)[k千]?', salary_str)
        if match_k:
            min_val = float(match_k.group(1))
            max_val = float(match_k.group(2))
            return (min_val, max_val)
        
        return None
    
    @staticmethod
    def analyze_data(df):
        """
        分析清洗后的数据，生成统计信息
        
        Args:
            df: pandas DataFrame
            
        Returns:
            dict: 统计信息
        """
        stats = {}
        try:
            stats["总职位数"] = len(df)
            if "平均薪资(K)" in df.columns:
                stats["平均薪资(K)"] = round(df["平均薪资(K)"].dropna().mean(), 2)
                stats["最高薪资(K)"] = round(df["最高薪资(K)"].dropna().max(), 2)
                stats["最低薪资(K)"] = round(df["最低薪资(K)"].dropna().min(), 2)
            
            if "公司名称" in df.columns:
                stats["公司数量"] = df["公司名称"].nunique()
                stats["招聘职位最多的公司"] = df["公司名称"].value_counts().head(5).to_dict()
            
            if "工作地点" in df.columns:
                stats["职位最多的地区"] = df["工作地点"].value_counts().head(5).to_dict()
            
            logger.info("数据分析完成")
        except Exception as e:
            logger.error(f"数据分析出错: {e}")
        return stats
