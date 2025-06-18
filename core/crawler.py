import time
import random
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)

from utils.logger import logger
from config.settings import URLS, SELECTORS, RANDOM_DELAY_MIN, RANDOM_DELAY_MAX

class BaseCrawler:
    """爬虫基类，包含通用方法"""

    def __init__(self, driver, site_name):
        self.driver = driver
        self.site_name = site_name
        self.search_url_template = URLS[site_name]["search"]
        self.selectors = SELECTORS[site_name]["search"]
        self.job_data = []
        self.retry_count = 0

    def _random_sleep(self, min_time=None, max_time=None):
        """随机延时，模拟人工浏览"""
        min_time = min_time or RANDOM_DELAY_MIN
        max_time = max_time or RANDOM_DELAY_MAX
        sleep_time = random.uniform(min_time, max_time)
        time.sleep(sleep_time)

    def _wait_for_job_list(self):
        """等待职位列表加载完成"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["job_list"]))
            )
        except TimeoutException:
            logger.warning("等待职位列表加载超时，尝试刷新页面")
            self.driver.refresh()
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors["job_list"]))
            )

    def _extract_job_item(self, job_item):
        """从职位项中提取数据"""
        try:
            return {
                "职位名称": job_item.find_element(By.CSS_SELECTOR, self.selectors["title"]).text.strip(),
                "公司名称": job_item.find_element(By.CSS_SELECTOR, self.selectors["company_name"]).text.strip(),
                "薪资": job_item.find_element(By.CSS_SELECTOR, self.selectors["salary"]).text.strip(),
                "工作地点": job_item.find_element(By.CSS_SELECTOR, self.selectors["location"]).text.strip()
            }
        except NoSuchElementException as e:
            logger.warning(f"提取职位数据时未找到元素: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"提取职位数据时发生错误: {str(e)}")
            return None

    def save_to_excel(self, filename):
        """将爬取的数据保存到Excel文件"""
        if not self.job_data:
            logger.warning("没有数据可保存")
            return False
        try:
            df = pd.DataFrame(self.job_data)
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            logger.error(f"保存数据到Excel时发生错误: {str(e)}")
            return False

class ZhilianCrawler(BaseCrawler):
    """智联招聘爬虫（带分页功能）"""

    def __init__(self, driver):
        super().__init__(driver, "zhilian")
        self.current_page = 1

    def search_jobs(self, keyword, max_pages=5):
        """搜索职位并爬取数据（带分页）"""
        logger.info(f"开始在智联招聘搜索 '{keyword}'，最大页数: {max_pages}")

        try:
            search_url = self.search_url_template.format(keyword=keyword)
            self.driver.get(search_url)

            while self.current_page <= max_pages:
                logger.info(f"正在处理第 {self.current_page}/{max_pages} 页")

                self._wait_for_job_list()
                self._random_sleep(2, 3)

                page_data = self._extract_page_data()
                if page_data:
                    self.job_data.extend(page_data)
                    logger.info(f"第 {self.current_page} 页获取到 {len(page_data)} 条数据")
                else:
                    logger.warning(f"第 {self.current_page} 页未获取到数据")

                if not self._go_to_next_page():
                    logger.info("无法翻页，可能已达最后一页")
                    break

                self.current_page += 1

            logger.info(f"爬取完成，共获取 {len(self.job_data)} 条数据")
            return self.job_data

        except Exception as e:
            logger.error(f"爬取失败: {str(e)}")
            return self.job_data

    def _extract_page_data(self):
        """提取当前页数据"""
        try:
            items = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["job_item"])
            return [self._parse_job_item(item) for item in items if item]
        except Exception as e:
            logger.error(f"提取页面数据失败: {str(e)}")
            return []

    def _parse_job_item(self, item):
        """解析单个职位项"""
        try:
            return {
                "职位名称": item.find_element(By.CSS_SELECTOR, self.selectors["title"]).text,
                "公司名称": item.find_element(By.CSS_SELECTOR, self.selectors["company"]).text,
                "薪资": item.find_element(By.CSS_SELECTOR, self.selectors["salary"]).text,
                "工作地点": item.find_element(By.CSS_SELECTOR, self.selectors["location"]).text,
                "页码": self.current_page
            }
        except NoSuchElementException as e:
            logger.warning(f"提取职位信息时元素未找到: {str(e)}")
            return None

    def _go_to_next_page(self):
        """跳转到下一页"""
        try:
            next_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors["next_page"]))
            )

            self.driver.execute_script("arguments[0].scrollIntoView()", next_btn)
            self._random_sleep(1, 2)
            next_btn.click()

            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_element(
                    By.CSS_SELECTOR,
                    f"{self.selectors['current_page']}"
                ).text == str(self.current_page + 1)
            )

            return True

        except TimeoutException:
            logger.warning("下一页按钮不可用或超时")
            return False
        except Exception as e:
            logger.warning(f"翻页失败: {str(e)}")
            return False
