# 柱状图：不同入口下各个提问需求维度数量

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'KaiTi'  # 设置为宋体

# 读取Excel文件
file_path = r'C:\Users\wps\Desktop\111\数据分析\合并后的分析结果1.xlsx'
df = pd.read_excel(file_path)

# 去除列名为"pc_copilot"的数据
df_filtered = df[df['数据来源'] != 'pc_copilot']

# 统计每个数据来源的三个列中为“是”的数量
yes_counts = df_filtered.groupby('数据来源')[['生成创作', '获取信息', '内容改进']].apply(lambda x: (x == '是').sum()).reset_index()

# 绘制柱状图
fig, ax = plt.subplots(figsize=(10, 6))

# 柱状图的宽度
bar_width = 0.25
index = range(len(yes_counts))

# 绘制每个列的柱状图
bars1 = ax.bar([i - bar_width for i in index], yes_counts['生成创作'], bar_width, label='生成创作',color='#FFCCCC')
bars2 = ax.bar(index, yes_counts['获取信息'], bar_width, label='获取信息',color='#CC99CC')
bars3 = ax.bar([i + bar_width for i in index], yes_counts['内容改进'], bar_width, label='内容改进',color='#CCCCFF')

# 添加数据标签
def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

add_labels(bars1)
add_labels(bars2)
add_labels(bars3)

# 设置图表标题和标签
ax.set_xlabel('数据来源', fontsize=14)
ax.set_ylabel('各个提问需求维度数量', fontsize=14)
ax.set_title('不同入口下各个提问需求维度数量', fontsize=16)
ax.set_xticks(index)
ax.set_xticklabels(yes_counts['数据来源'])
ax.legend()

# 调整布局
plt.tight_layout()

# 显示图表
plt.show()