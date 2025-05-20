from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
from suburbs import SUBURBS
import json
from datetime import datetime
import platform

class PropertyAnalyzer:
    def __init__(self):
        self.setup_driver()
        self.data = []

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 根据系统类型选择合适的ChromeDriver
        system = platform.system()
        arch = platform.machine()
        
        if system == "Darwin":  # macOS
            if arch == "arm64":
                options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

    def extract_property_data(self, url):
        try:
            self.driver.get(url)
            time.sleep(2)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "suburb-statistics"))
            )

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            suburb_name = url.split('/')[-1].replace('-', ' ').title()
            
            stats = {'suburb': suburb_name}
            stats_container = soup.find('div', class_='suburb-statistics')
            
            if stats_container:
                all_stats = stats_container.find_all('div', class_='stat-item')
                for stat in all_stats:
                    label = stat.find('div', class_='label')
                    value = stat.find('div', class_='value')
                    if label and value:
                        label_text = label.text.strip()
                        value_text = value.text.strip()
                        stats[label_text] = value_text

            # 打印当前suburb的信息
            print(f"\n获取到 {suburb_name} 的数据:")
            for key, value in stats.items():
                if key != 'suburb':
                    print(f"- {key}: {value}")

            return stats
        except Exception as e:
            print(f"处理 {url} 时出错: {str(e)}")
            return None

    def analyze_suburbs(self, urls):
        for url in tqdm(urls, desc="分析郊区"):
            data = self.extract_property_data(url)
            if data:
                self.data.append(data)
            time.sleep(1)

    def save_results(self, filename='property_analysis.csv'):
        if not self.data:
            print("没有数据可以保存")
            return
            
        df = pd.DataFrame(self.data)
        
        # 保存CSV
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到 {filename}")
        
        # 生成Markdown报告
        self.generate_markdown_report(df)
        
        # 生成JSON数据
        self.save_json_data(df)

    def generate_markdown_report(self, df):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open('property_report.md', 'w', encoding='utf-8') as f:
            # 写入标题和更新时间
            f.write(f"# 墨尔本房产市场分析报告\n\n")
            f.write(f"*更新时间：{current_time}*\n\n")
            
            # 总体统计
            f.write("## 总体统计\n\n")
            f.write(f"- 分析郊区数量：{len(df)}\n\n")
            
            # 中位数房价排名
            f.write("## 房价排名 (中位数)\n\n")
            f.write("| 排名 | 郊区 | 中位价格 | 年度涨幅 | 租金回报率 |\n")
            f.write("|------|------|----------|----------|------------|\n")
            
            # 按中位数房价排序
            price_sorted = df.sort_values(by='中位价格', ascending=False)
            for idx, row in price_sorted.iterrows():
                f.write(f"| {idx + 1} | {row['suburb']} | {row.get('中位价格', 'N/A')} | {row.get('年度涨幅', 'N/A')} | {row.get('租金回报率', 'N/A')} |\n")
            
            f.write("\n## 投资回报率排名\n\n")
            f.write("| 排名 | 郊区 | 租金回报率 | 中位价格 | 年度涨幅 |\n")
            f.write("|------|------|------------|----------|----------|\n")
            
            # 按租金回报率排序
            yield_sorted = df.sort_values(by='租金回报率', ascending=False)
            for idx, row in yield_sorted.iterrows():
                f.write(f"| {idx + 1} | {row['suburb']} | {row.get('租金回报率', 'N/A')} | {row.get('中位价格', 'N/A')} | {row.get('年度涨幅', 'N/A')} |\n")
            
            f.write("\n## 年度涨幅排名\n\n")
            f.write("| 排名 | 郊区 | 年度涨幅 | 中位价格 | 租金回报率 |\n")
            f.write("|------|------|----------|----------|------------|\n")
            
            # 按年度涨幅排序
            growth_sorted = df.sort_values(by='年度涨幅', ascending=False)
            for idx, row in growth_sorted.iterrows():
                f.write(f"| {idx + 1} | {row['suburb']} | {row.get('年度涨幅', 'N/A')} | {row.get('中位价格', 'N/A')} | {row.get('租金回报率', 'N/A')} |\n")
        
        print(f"\nMarkdown报告已保存到 property_report.md")

    def save_json_data(self, df):
        # 转换为JSON格式
        json_data = {
            'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_suburbs': len(df),
            'suburbs_data': df.to_dict('records')
        }
        
        with open('property_data.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON数据已保存到 property_data.json")

    def close(self):
        self.driver.quit()

def main():
    analyzer = PropertyAnalyzer()
    try:
        print(f"开始分析 {len(SUBURBS)} 个郊区...")
        analyzer.analyze_suburbs(SUBURBS)
        analyzer.save_results()
    finally:
        analyzer.close()

if __name__ == "__main__":
    main() 