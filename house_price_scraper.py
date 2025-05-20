import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import subprocess

def setup_driver():
    """设置并返回Chrome WebDriver"""
    try:
        chrome_options = Options()
        # 暂时移除headless模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # 添加实验性选项
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        print("正在初始化Chrome浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 执行一些JavaScript来避免检测
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"创建WebDriver时发生错误: {e}")
        return None

def get_property_data():
    url = "https://www.onthehouse.com.au/suburb/vic/glen-waverley-3150"
    
    try:
        print("正在启动Chrome浏览器...")
        driver = setup_driver()
        if not driver:
            print("无法初始化Chrome浏览器")
            return None
            
        print("正在访问目标网页...")
        driver.get(url)
        
        print("等待页面加载...")
        wait = WebDriverWait(driver, 30)
        
        try:
            # 等待页面加载完成并提取文本
            print("查找房产信息...")
            
            # 提取涨幅信息
            increase_text = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Houses in Glen Waverley have seen a')]"))).text
            print(f"找到涨幅文本: {increase_text}")
            
            # 提取中位价值信息
            value_text = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'The median value for Houses in Glen Waverley is')]"))).text
            print(f"找到价值文本: {value_text}")
            
            # 使用正则表达式提取数据
            house_increase = float(re.search(r'Houses in Glen Waverley have seen a ([\d.]+)%', increase_text).group(1))
            unit_increase = float(re.search(r'Units have seen a ([\d.]+)%', increase_text).group(1))
            
            house_value = float(re.search(r'Houses in Glen Waverley is \$([\d,]+)', value_text).group(1).replace(',', ''))
            unit_value = float(re.search(r'Units is \$([\d,]+)', value_text).group(1).replace(',', ''))
            
            return {
                'house_increase': house_increase,
                'unit_increase': unit_increase,
                'house_value': house_value,
                'unit_value': unit_value
            }
            
        except Exception as e:
            print(f"处理数据时发生错误: {str(e)}")
            print("页面内容:", driver.page_source)
            driver.quit()
            return None
            
    except Exception as e:
        print(f"访问网页时发生错误: {str(e)}")
        try:
            driver.quit()
        except:
            pass
        return None

def analyze_prices(df):
    if df is None or df.empty:
        print("没有可用的数据进行分析")
        return
    
    # 只分析有效的价格数据
    df_valid = df[pd.to_numeric(df['price'], errors='coerce').notna()]
    
    if df_valid.empty:
        print("没有有效的价格数据进行分析")
        return
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 计算不同时间点的平均价格
    def get_average_price_for_period(target_date):
        mask = (df_valid['date'] >= target_date) & (df_valid['date'] <= current_date)
        period_data = df_valid[mask]
        if not period_data.empty:
            return period_data['price'].mean(), period_data['date'].min()
        return None, None
    
    one_year_ago = current_date - timedelta(days=365)
    five_years_ago = current_date - timedelta(days=365*5)
    ten_years_ago = current_date - timedelta(days=365*10)
    
    current_avg = df_valid[df_valid['date'] >= current_date - timedelta(days=30)]['price'].mean()
    one_year_avg, one_year_date = get_average_price_for_period(one_year_ago)
    five_year_avg, five_year_date = get_average_price_for_period(five_years_ago)
    ten_year_avg, ten_year_date = get_average_price_for_period(ten_years_ago)
    
    # 打印结果
    print(f"\n房价分析结果:")
    print(f"当前平均价格: ${current_avg:,.2f}" if pd.notna(current_avg) else "当前平均价格: 数据不可用")
    
    if one_year_avg is not None:
        print(f"一年前平均价格 ({one_year_date.strftime('%Y-%m-%d')}): ${one_year_avg:,.2f}")
        if pd.notna(current_avg):
            print(f"一年涨幅: {((current_avg - one_year_avg) / one_year_avg * 100):.2f}%")
    
    if five_year_avg is not None:
        print(f"五年前平均价格 ({five_year_date.strftime('%Y-%m-%d')}): ${five_year_avg:,.2f}")
        if pd.notna(current_avg):
            print(f"五年涨幅: {((current_avg - five_year_avg) / five_year_avg * 100):.2f}%")
    
    if ten_year_avg is not None:
        print(f"十年前平均价格 ({ten_year_date.strftime('%Y-%m-%d')}): ${ten_year_avg:,.2f}")
        if pd.notna(current_avg):
            print(f"十年涨幅: {((current_avg - ten_year_avg) / ten_year_avg * 100):.2f}%")
    
    # 按房产类型分组分析
    if 'type' in df_valid.columns:
        print("\n各类型房产的平均价格:")
        type_analysis = df_valid.groupby('type')['price'].agg(['mean', 'count']).round(2)
        print(type_analysis)
    
    # 绘制价格趋势图
    plt.figure(figsize=(12, 6))
    plt.scatter(df_valid['date'], df_valid['price'], alpha=0.5)
    plt.title('Glen Waverley房价趋势')
    plt.xlabel('年份')
    plt.ylabel('价格 ($)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('price_trend.png')
    plt.close()

def main():
    print("正在获取Glen Waverley的房产数据...")
    data = get_property_data()
    if data is not None:
        print("\nGlen Waverley房产数据分析:")
        print(f"房屋5年涨幅: {data['house_increase']}%")
        print(f"房屋中位价值: ${data['house_value']:,.2f}")
        print(f"公寓5年涨幅: {data['unit_increase']}%")
        print(f"公寓中位价值: ${data['unit_value']:,.2f}")
    else:
        print("无法获取房产数据，请检查网络连接或网站可用性。")

if __name__ == "__main__":
    main() 