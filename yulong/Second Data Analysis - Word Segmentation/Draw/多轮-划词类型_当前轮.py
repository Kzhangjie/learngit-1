import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体显示中文
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-多.xlsx'

# 读取Excel文件
df = pd.read_excel(excel_file)

# 检查数据类型
print(df.dtypes)

# 按划词类型和轮次分组并计数
grouped = df.groupby(['划词类型', '轮次']).size().reset_index(name='数量')

# 将数据重塑为矩阵形式
heatmap_data = grouped.pivot(index='划词类型', columns='轮次', values='数量').fillna(0)

# 绘制热力图
plt.figure(figsize=(12, 8))
sns.heatmap(heatmap_data, annot=True, cmap='YlGnBu', linewidths=0.5)

plt.title('划词类型与轮次的关联度热力图', fontsize=16)
plt.xlabel('轮次', fontsize=14)
plt.ylabel('划词类型', fontsize=14)
plt.tight_layout()
plt.show()