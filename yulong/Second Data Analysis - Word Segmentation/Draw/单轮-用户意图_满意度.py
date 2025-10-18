import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以根据需要选择其他中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-单.xlsx'

# 读取Excel文件
df_filtered = pd.read_excel(excel_file)

# 创建交叉表（不使用normalize参数来获取数值而不是比例）
crosstab = pd.crosstab(df_filtered['用户意图'], df_filtered['满意度'])

# 检查满意度列是否为数值类型
# 如果不是数值类型，转换为数值类型
crosstab.columns = pd.to_numeric(crosstab.columns, errors='coerce')

# 对满意度进行排序
sorted_satisfaction = sorted(crosstab.columns)
sorted_crosstab = crosstab[sorted_satisfaction]

# 绘制热力图
plt.figure(figsize=(12, 8))
sns.heatmap(sorted_crosstab, annot=True, cmap='YlGnBu', fmt='d', linewidths=0.5)
plt.title('用户意图与满意度交叉分析热力图', fontsize=16)
plt.xlabel('满意度', fontsize=12)
plt.ylabel('用户意图', fontsize=12)
plt.tight_layout()
plt.show()

# 可选：显示统计信息
print("用户意图与满意度交叉表")
print(sorted_crosstab)