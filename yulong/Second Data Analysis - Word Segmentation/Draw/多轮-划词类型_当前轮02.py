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

# 筛选轮次在1到10之间的数据
df_filtered = df[(df['轮次'] >= 1) & (df['轮次'] <= 10)]

# 按划词类型和轮次分组并计数
grouped = df_filtered.groupby(['划词类型', '轮次']).size().reset_index(name='数量')

# 将数据重塑为矩阵形式
heatmap_data = grouped.pivot(index='划词类型', columns='轮次', values='数量').fillna(0)

# 确保显示1到10的所有轮次（即使某些轮次没有数据）
if heatmap_data.shape[1] < 10:
    for i in range(1, 11):
        if i not in heatmap_data.columns:
            heatmap_data[i] = 0
    # 重新排序列
    heatmap_data = heatmap_data[sorted(heatmap_data.columns)]

# 绘制热力图
plt.figure(figsize=(12, 8))
sns.heatmap(heatmap_data, annot=True, cmap='YlGnBu', linewidths=0.5)

plt.title('划词类型与轮次的关联度热力图（轮次1-10）', fontsize=16)
plt.xlabel('轮次', fontsize=14)
plt.ylabel('划词类型', fontsize=14)
plt.tight_layout()
plt.show()    