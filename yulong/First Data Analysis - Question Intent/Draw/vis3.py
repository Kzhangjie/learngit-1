# 折线图：不同时间段下各个维度提问需求量趋势

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] =  'KaiTi'  # 设置为宋体

# 读取Excel文件
file_path = r'C:\Users\wps\Desktop\111\数据可视化\正式\合并后的分析结果1.xlsx'
df = pd.read_excel(file_path)

# 统计每个时间段和维度为“是”的数量
yes_counts = df.groupby(['时间'])[['生成创作', '获取信息', '内容改进']].apply(lambda x: (x == '是').sum()).reset_index()

# 统计每个时间段的总数据量
total_counts = df.groupby('时间').size().reset_index(name='总数量')

# 合并数据以计算比例
merged_df = pd.merge(yes_counts, total_counts, on='时间')

# 计算每个维度的比例
for column in ['生成创作', '获取信息', '内容改进']:
    merged_df[f'{column}_比例'] = merged_df[column] / merged_df['总数量']

# 绘制折线图
plt.figure(figsize=(12, 6))

# 为每个维度绘制折线图
for column in ['生成创作', '获取信息', '内容改进']:
    plt.plot(merged_df['时间'], merged_df[f'{column}_比例'], marker='o', label=column)

    # 添加数据标签（显示比例）
    for x, y in zip(merged_df['时间'], merged_df[f'{column}_比例']):
        plt.text(x, y + 0.01, f'{y:.2%}', ha='center', va='bottom')

# 设置图表标题和标签
plt.title('不同时间段下各个提问需求维度比例趋势', fontsize=16)
plt.xlabel('时间段', fontsize=14)
plt.ylabel('比例', fontsize=14)
plt.legend()

# 调整x轴标签角度，使标签更易读
plt.xticks(rotation=45)

# 调整布局
plt.tight_layout()

# 显示图表
plt.show()