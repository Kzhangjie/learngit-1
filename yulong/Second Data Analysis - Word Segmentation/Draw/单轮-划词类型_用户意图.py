import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以根据需要选择其他中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-单.xlsx'

# 读取Excel文件
df_filtered = pd.read_excel(excel_file)

# 创建划词类型与用户意图的交叉表
crosstab = pd.crosstab(df_filtered['划词类型'], df_filtered['用户意图'])

# 计算卡方检验
chi2, p_value, dof, expected = chi2_contingency(crosstab)
print(f"卡方检验统计量：{chi2}")
print(f"p 值：{p_value}")

# 计算关联度（Cramer's V）
n = crosstab.sum().sum()
min_dim = min(crosstab.shape) - 1
cramers_v = np.sqrt(chi2 / (n * min_dim))
print(f"Cramer's V 关联度：{cramers_v}")

# 绘制热力图
plt.figure(figsize=(12, 8))
sns.heatmap(crosstab, annot=True, cmap='YlGnBu', fmt='d', linewidths=0.5)

plt.title('划词类型与用户意图关联度热力图', fontsize=16)
plt.xlabel('用户意图', fontsize=12)
plt.ylabel('划词类型', fontsize=12)
plt.tight_layout()

# 调整Y轴标签角度，避免重叠
plt.yticks(rotation=0)

plt.show()

# 输出交叉表统计数据
print("划词类型与用户意图交叉表：")
print(crosstab)