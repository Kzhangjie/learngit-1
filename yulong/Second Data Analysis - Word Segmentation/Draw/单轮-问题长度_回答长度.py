import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以根据需要选择其他中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-单.xlsx'

# 读取Excel文件
df= pd.read_excel(excel_file)

# 数据预处理：确保问题长度与回答长度为数值类型
df['问题长度'] = pd.to_numeric(df['问题长度'], errors='coerce')
df['回答长度'] = pd.to_numeric(df['回答长度'], errors='coerce')

# 剔除无效值
df_valid = df.dropna(subset=['问题长度', '回答长度'])

# 计算相关系数
correlation, p_value = pearsonr(df_valid['问题长度'], df_valid['回答长度'])

# 绘制散点图
plt.figure(figsize=(12, 8))
scatter = sns.scatterplot(x='问题长度', y='回答长度', data=df_valid, alpha=0.6)
plt.title(f'问题长度与回答长度的相关性（相关系数：{correlation:.2f}）', fontsize=16)
plt.xlabel('问题长度', fontsize=12)
plt.ylabel('回答长度', fontsize=12)

# 添加趋势线
sns.regplot(x='问题长度', y='回答长度', data=df_valid, scatter=False, color='red')

plt.tight_layout()
plt.show()

# 输出统计信息
print(f"问题长度与回答长度的相关系数：{correlation:.2f}")
print(f"p 值：{p_value:.4f}")