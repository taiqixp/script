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
import random
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from collections import defaultdict

# 测试用的郊区列表
TEST_SUBURBS = [
    "https://www.onthehouse.com.au/suburb/vic/box-hill-3128",
    "https://www.onthehouse.com.au/suburb/vic/glen-waverley-3150",
    "https://www.onthehouse.com.au/suburb/vic/mount-waverley-3149",
    "https://www.onthehouse.com.au/suburb/vic/burwood-3125",
    "https://www.onthehouse.com.au/suburb/vic/clayton-south-3169",
    "https://www.onthehouse.com.au/suburb/vic/springvale-3171",
    "https://www.onthehouse.com.au/suburb/vic/keysborough-3173",
    "https://www.onthehouse.com.au/suburb/vic/dandenong-3175",
    "https://www.onthehouse.com.au/suburb/vic/noble-park-3174",
    "https://www.onthehouse.com.au/suburb/vic/wheelers-hill-3150",
    "https://www.onthehouse.com.au/suburb/vic/vermont-south-3133",
    "https://www.onthehouse.com.au/suburb/vic/doncaster-3108",
    "https://www.onthehouse.com.au/suburb/vic/frankston-3199",
    "https://www.onthehouse.com.au/suburb/vic/frankston-south-3199",
    "https://www.onthehouse.com.au/suburb/vic/berwick-3806",
    "https://www.onthehouse.com.au/suburb/vic/cranbourne-3977",
    "https://www.onthehouse.com.au/suburb/vic/officer-3809",
    "https://www.onthehouse.com.au/suburb/vic/pakenham-3810",
    "https://www.onthehouse.com.au/suburb/vic/caulfield-3162",
    "https://www.onthehouse.com.au/suburb/vic/bentleigh-east-3165",
    "https://www.onthehouse.com.au/suburb/vic/forest-hill-3131",
    "https://www.onthehouse.com.au/suburb/vic/bayswater-north-3153",
    "https://www.onthehouse.com.au/suburb/vic/wantirna-south-3152",
    "https://www.onthehouse.com.au/suburb/vic/wantirna-3152",
    "https://www.onthehouse.com.au/suburb/vic/surrey-hills-3127",
    "https://www.onthehouse.com.au/suburb/vic/balwyn-3103",
    "https://www.onthehouse.com.au/suburb/vic/camberwell-3124",
    "https://www.onthehouse.com.au/suburb/vic/kew-3101",
    "https://www.onthehouse.com.au/suburb/vic/toorak-3142",
    "https://www.onthehouse.com.au/suburb/vic/malvern-3144",
    "https://www.onthehouse.com.au/suburb/vic/glen-iris-3146",
    "https://www.onthehouse.com.au/suburb/vic/hawthorn-3122",
    "https://www.onthehouse.com.au/suburb/vic/canterbury-3126",
    "https://www.onthehouse.com.au/suburb/vic/brighton-3186"
]

def setup_driver():
    """设置并返回Chrome WebDriver"""
    try:
        chrome_options = Options()
        
        # 基本设置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 高级反检测设置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 随机User-Agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # 添加其他headers
        chrome_options.add_argument('--accept-language=en-US,en;q=0.9')
        chrome_options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8')
        
        print("正在初始化Chrome浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 执行JavaScript来避免检测
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        
        return driver
    except Exception as e:
        print(f"创建WebDriver时发生错误: {e}")
        return None

def random_sleep():
    """随机等待一段时间"""
    base_delay = random.uniform(1, 3)  # 基础延迟8-15秒
    extra_delay = random.uniform(0, 3)   # 额外随机延迟0-5秒
    time.sleep(base_delay + extra_delay)

def get_property_data(url, driver):
    """获取单个郊区的房产数据"""
    suburb_name = url.split('/')[-1].replace('-', ' ').title()
    print(f"\n正在获取 {suburb_name} 的数据...")
    
    try:
        driver.get(url)
        random_sleep()
        
        # 随机滚动页面
        for _ in range(3):
            driver.execute_script(f"window.scrollTo(0, {random.randint(100, 500)})")
            random_sleep()
        
        wait = WebDriverWait(driver, 30)
        
        try:
            # 等待页面加载完成并提取文本
            print("等待页面加载...")
            
            # 尝试多种选择器
            selectors = [
                "//div[contains(text(), 'properties') and contains(text(), 'median value')]",
                "//p[contains(text(), 'properties') and contains(text(), 'median value')]",
                "//*[contains(text(), 'properties') and contains(text(), 'median value')]"
            ]
            
            stats_text = None
            for selector in selectors:
                try:
                    element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    stats_text = element.text
                    if stats_text:
                        break
                except:
                    continue
            
            if not stats_text:
                print("无法找到统计数据")
                return None
                
            print(f"找到统计文本: {stats_text}")
            
            # 提取数据，同时处理increase和decrease
            house_change_match = re.search(r'Houses in [^%]+ ([-\d.]+)% (?:increase|decrease)', stats_text)
            unit_change_match = re.search(r'Units have seen a ([-\d.]+)% (?:increase|decrease)', stats_text)
            
            # 分别检查house和unit是increase还是decrease
            house_increase = 0
            unit_increase = 0
            
            if house_change_match:
                # 提取house部分的文本来判断是increase还是decrease
                house_text = re.search(r'Houses[^,]+(?:increase|decrease)', stats_text)
                house_value = float(house_change_match.group(1))
                
                # 如果是decrease且数值为正，则变为负数
                # 如果数值已经是负数，则保持不变
                if house_text and 'decrease' in house_text.group() and house_value > 0:
                    house_increase = -house_value
                else:
                    house_increase = house_value
                    
            if unit_change_match:
                # 提取unit部分的文本来判断是increase还是decrease
                unit_text = re.search(r'Units[^,]+(?:increase|decrease)', stats_text)
                unit_value = float(unit_change_match.group(1))
                
                # 如果是decrease且数值为正，则变为负数
                # 如果数值已经是负数，则保持不变
                if unit_text and 'decrease' in unit_text.group() and unit_value > 0:
                    unit_increase = -unit_value
                else:
                    unit_increase = unit_value
            
            # 尝试从同一段文本中提取价值信息
            value_text = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'median value') and contains(text(), '$')]"))).text
            print(f"找到价值文本: {value_text}")
            
            house_value_match = re.search(r'Houses in [^\$]+\$([\d,]+)', value_text)
            unit_value_match = re.search(r'Units is \$([\d,]+)', value_text)
            
            if not all([house_change_match, unit_change_match, house_value_match, unit_value_match]):
                print("无法从页面提取完整数据，尝试备用提取方法...")
                
                # 获取完整页面文本
                full_text = driver.find_element(By.TAG_NAME, "body").text
                print("页面完整文本：")
                print(full_text)
                
                # 重新尝试匹配，使用更宽松的模式
                house_change_match = house_change_match or re.search(r'Houses[^%]+([-\d.]+)% (?:increase|decrease)', full_text)
                unit_change_match = unit_change_match or re.search(r'Units[^%]+([-\d.]+)% (?:increase|decrease)', full_text)
                house_value_match = house_value_match or re.search(r'Houses[^\$]+\$([\d,]+)', full_text)
                unit_value_match = unit_value_match or re.search(r'Units[^\$]+\$([\d,]+)', full_text)
                
                # 再次检查decrease情况（如果之前没有匹配到）
                if house_change_match and house_increase == 0:
                    house_text = re.search(r'Houses[^,]+(?:increase|decrease)', full_text)
                    house_value = float(house_change_match.group(1))
                    
                    if house_text and 'decrease' in house_text.group() and house_value > 0:
                        house_increase = -house_value
                    else:
                        house_increase = house_value
                        
                if unit_change_match and unit_increase == 0:
                    unit_text = re.search(r'Units[^,]+(?:increase|decrease)', full_text)
                    unit_value = float(unit_change_match.group(1))
                    
                    if unit_text and 'decrease' in unit_text.group() and unit_value > 0:
                        unit_increase = -unit_value
                    else:
                        unit_increase = unit_value
                
                if not all([house_change_match, unit_change_match, house_value_match, unit_value_match]):
                    print("备用提取方法也失败了")
                    return None
            
            # 提取日期信息
            date_match = re.search(r'As at (\d+ \w+ \d+)', stats_text)
            if not date_match:
                # 尝试从完整页面文本中查找
                full_text = driver.find_element(By.TAG_NAME, "body").text
                date_match = re.search(r'As at (\d+ \w+ \d+)', full_text)
            
            if date_match:
                # 解析日期，例如 "30 April 2025"
                report_date = datetime.strptime(date_match.group(1), '%d %B %Y').strftime('%Y.%m.%d')
                print(f"从网页提取到日期: {date_match.group(1)} -> {report_date}")
            else:
                # 使用当前月份减1作为日期
                current_date = datetime.now()
                if current_date.month == 1:
                    # 如果是1月，则变为去年12月
                    last_month_date = current_date.replace(year=current_date.year - 1, month=12)
                else:
                    last_month_date = current_date.replace(month=current_date.month - 1)
                report_date = last_month_date.strftime('%Y.%m.%d')
                print(f"未找到日期信息，使用计算的日期: {report_date}")
            
            # 提取并转换数据，移除逗号
            house_value = float(house_value_match.group(1).replace(',', ''))
            unit_value = float(unit_value_match.group(1).replace(',', ''))
            
            # 提取租金信息
            rent_text = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'median rent')]"))).text
            print(f"找到租金文本: {rent_text}")
            
            house_rent_match = re.search(r'Houses have a median rent of \$([\d,]+)', rent_text)
            unit_rent_match = re.search(r'Units have a median rent of \$([\d,]+)', rent_text)
            
            if not all([house_rent_match, unit_rent_match]):
                print("无法从页面提取租金数据，尝试备用提取方法...")
                house_rent_match = re.search(r'Houses have a median rent of \$([\d,]+)', full_text)
                unit_rent_match = re.search(r'Units have a median rent of \$([\d,]+)', full_text)
            
            # 提取并转换数据，移除逗号
            house_rent = float(house_rent_match.group(1).replace(',', '')) if house_rent_match else None
            unit_rent = float(unit_rent_match.group(1).replace(',', '')) if unit_rent_match else None
            
            # 计算租金回报率
            house_yield = f"{(house_rent * 52 / house_value * 100):.2f}%" if house_rent else "-"
            unit_yield = f"{(unit_rent * 52 / unit_value * 100):.2f}%" if unit_rent else "-"
            
            return {
                'suburb': suburb_name,
                'date': report_date,
                'house_increase': house_increase,
                'unit_increase': unit_increase,
                'house_value': house_value,
                'unit_value': unit_value,
                'house_rent': house_rent,
                'unit_rent': unit_rent,
                'house_yield': house_yield,
                'unit_yield': unit_yield
            }
            
        except TimeoutException:
            print(f"等待页面元素超时")
            return None
        except Exception as e:
            print(f"处理数据时发生错误: {str(e)}")
            return None
            
    except Exception as e:
        print(f"访问网页时发生错误: {str(e)}")
        return None

def save_results(data, filename='suburb_analysis.md', append_mode=False):
    """保存分析结果为Markdown格式，支持追加模式"""
    if not data:
        print("没有数据可以保存")
        return
        
    # 如果是第一次写入，创建文件头
    if not append_mode or not os.path.exists(filename):
        mode = 'w'
        write_header = True
    else:
        mode = 'a'
        write_header = False
        
    with open(filename, mode, encoding='utf-8') as f:
        if write_header:
            f.write("# 墨尔本房产市场分析报告\n\n")
            f.write(f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("| 日期 | 地区 | 类型 | 价格 | 近五年涨幅 | 周租金 | 租金回报率 |\n")
            f.write("|------|------|------|------|------------|--------|------------|\n")
        
        # 写入数据行
        if isinstance(data, list):
            suburb_data_list = data
        else:
            suburb_data_list = [data]
            
        for suburb_data in suburb_data_list:
            suburb = suburb_data['suburb']
            # 写入house数据
            house_rent = f"${suburb_data['house_rent']:.0f}" if suburb_data['house_rent'] else "-"
            f.write(f"| {suburb_data['date']} | {suburb} | house | ${suburb_data['house_value']:,.0f} | {suburb_data['house_increase']}% | {house_rent} | {suburb_data['house_yield']} |\n")
            # 写入unit数据
            unit_rent = f"${suburb_data['unit_rent']:.0f}" if suburb_data['unit_rent'] else "-"
            f.write(f"| {suburb_data['date']} | {suburb} | unit | ${suburb_data['unit_value']:,.0f} | {suburb_data['unit_increase']}% | {unit_rent} | {suburb_data['unit_yield']} |\n")
    
    print(f"\n数据已保存到 {filename}")
    
    # 打印分析结果
    print("\n分析结果:")
    for suburb_data in suburb_data_list:
        print(f"\n{suburb_data['suburb']}:")
        print(f"house中位价值: ${suburb_data['house_value']:,.2f}")
        print(f"house5年涨幅: {suburb_data['house_increase']}%")
        if suburb_data['house_rent']:
            print(f"house周租金: ${suburb_data['house_rent']:.2f}")
            print(f"house租金回报率: {suburb_data['house_yield']}")
        print(f"unit中位价值: ${suburb_data['unit_value']:,.2f}")
        print(f"unit5年涨幅: {suburb_data['unit_increase']}%")
        if suburb_data['unit_rent']:
            print(f"unit周租金: ${suburb_data['unit_rent']:.2f}")
            print(f"unit租金回报率: {suburb_data['unit_yield']}")

def read_existing_data(filename='suburb_analysis.md'):
    """读取现有的 Markdown 文件并返回已存在的日期和区域组合"""
    existing_data = set()
    if not os.path.exists(filename):
        return existing_data
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 跳过表头
        data_lines = [line for line in lines if '|' in line][2:]  # 跳过标题行和分隔行
        
        for line in data_lines:
            parts = [part.strip() for part in line.split('|')[1:-1]]  # 去掉首尾的 |
            if len(parts) >= 2:  # 确保有足够的数据
                date = parts[0].strip()
                suburb = parts[1].strip()
                # 添加日期和地区的组合
                existing_data.add((date, suburb))
                
        return existing_data
    except Exception as e:
        print(f"读取现有数据时发生错误: {str(e)}")
        return set()

def main():
    print("正在开始多郊区房产数据分析...")
    
    # 读取现有数据
    existing_data = read_existing_data()
    print(f"已有数据的记录数量: {len(existing_data)}")
    if existing_data:
        # 按日期分组显示
        data_by_date = defaultdict(list)
        for date, suburb in existing_data:
            data_by_date[date].append(suburb)
        
        print("\n已有数据分布:")
        for date in sorted(data_by_date.keys()):
            suburbs = data_by_date[date]
            # 只显示唯一的郊区名（去重）
            unique_suburbs = sorted(set(suburbs))
            print(f"  {date}: {len(unique_suburbs)} 个郊区")
    
    driver = None
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            driver = setup_driver()
            if not driver:
                print("无法初始化Chrome浏览器")
                return
            
            total_suburbs = len(TEST_SUBURBS)
            skipped_count = 0
            success_count = 0
            
            print(f"\n开始分析 {total_suburbs} 个郊区的数据...")
            for i, url in enumerate(TEST_SUBURBS, 1):
                try:
                    suburb_name = url.split('/')[-1].replace('-', ' ').title()
                    
                    print(f"\n处理进度: {i}/{total_suburbs}")
                    
                    # 预先计算预期的日期（上个月的最后一天）
                    current_date = datetime.now()
                    if current_date.month == 1:
                        # 如果是1月，则变为去年12月
                        last_month = current_date.replace(year=current_date.year - 1, month=12, day=31)
                    else:
                        # 获取上个月的最后一天
                        last_month = current_date.replace(month=current_date.month - 1, day=1)
                        # 计算上个月的最后一天
                        if last_month.month == 12:
                            next_month = last_month.replace(year=last_month.year + 1, month=1)
                        else:
                            next_month = last_month.replace(month=last_month.month + 1)
                        last_day_of_last_month = next_month - timedelta(days=1)
                        last_month = last_day_of_last_month
                    
                    expected_date = last_month.strftime('%Y.%m.%d')
                    
                    # 预先检查数据是否已存在
                    check_tuple = (expected_date, suburb_name)
                    
                    if check_tuple in existing_data:
                        print(f"{suburb_name} 在 {expected_date} 的数据已存在，跳过")
                        skipped_count += 1
                        continue
                    
                    # 如果数据不存在，才访问网页
                    data = get_property_data(url, driver)
                    if data:
                        # 再次检查实际日期（以防网页上的日期与预期不同）
                        actual_check_tuple = (data['date'], suburb_name)
                        
                        if actual_check_tuple in existing_data:
                            print(f"\n{suburb_name} 在 {data['date']} 的数据已存在，跳过")
                            skipped_count += 1
                        else:
                            # 立即保存单个区域的数据
                            save_results(data, append_mode=(success_count > 0 or len(existing_data) > 0))
                            success_count += 1
                            print(f"成功保存 {suburb_name} 的数据")
                    else:
                        print(f"无法获取 {suburb_name} 的数据")
                    random_sleep()  # 在请求之间随机等待
                except Exception as e:
                    print(f"处理 {url} 时发生错误: {str(e)}")
                    print("继续处理下一个郊区...")
                    continue
            
            print(f"\n任务完成:")
            print(f"成功分析了 {success_count}/{total_suburbs} 个郊区的数据")
            print(f"跳过了 {skipped_count} 个已有数据的郊区")
            print(f"md文件内容直接复制到前端ai，让他更新到page中")
            break  # 如果成功完成，跳出重试循环
            
        except Exception as e:
            retry_count += 1
            print(f"\n发生错误: {str(e)}")
            if retry_count < max_retries:
                print(f"将在10秒后进行第 {retry_count + 1} 次重试...")
                time.sleep(10)
            else:
                print("达到最大重试次数，程序退出")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

if __name__ == "__main__":
    main() 