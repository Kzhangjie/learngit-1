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

# 确保满意度列是数值类型
df_filtered['满意度'] = pd.to_numeric(df_filtered['满意度'], errors='coerce')

# 剔除无效的满意度值
df_valid = df_filtered.dropna(subset=['满意度'])

# 创建交叉表（不使用normalize参数来获取数值而不是比例）
crosstab = pd.crosstab(df_valid['划词类型'], df_valid['满意度'])

# 对满意度进行排序
sorted_satisfaction = sorted(crosstab.columns)
sorted_crosstab = crosstab[sorted_satisfaction]

# 绘制热力图
plt.figure(figsize=(12, 8))
sns.heatmap(sorted_crosstab, annot=True, cmap='YlGnBu', fmt='d', linewidths=0.5)
plt.title('划词类型与满意度交叉分析热力图（数值）', fontsize=16)
plt.xlabel('满意度', fontsize=12)
plt.ylabel('划词类型', fontsize=12)
plt.tight_layout()
plt.yticks(rotation=0)
plt.show()

# 输出交叉表统计数据
print("划词类型与满意度交叉表（数值）：")
print(sorted_crosstab)