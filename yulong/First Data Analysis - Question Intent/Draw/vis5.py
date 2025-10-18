import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 读取Excel文件
file_path = r'C:\Users\wps\Desktop\111\数据可视化\正式\合并后的分析结果1.xlsx'
df = pd.read_excel(file_path)

# 设置字体为楷体
plt.rcParams['font.family'] = 'KaiTi'

# 将 '是' 转换为 1，'否' 转换为 0
for col in ['生成创作', '获取信息', '内容改进']:
    df[col] = df[col].apply(lambda x: 1 if x == '是' else 0)

# 按轮次分组并计算每个分组在各需求维度上的总值
grouped_data = df.groupby('轮次')[['生成创作', '获取信息', '内容改进']].sum().reset_index()

# 准备热力图数据
heatmap_data = grouped_data[['生成创作', '获取信息', '内容改进']].values.T  # 转置，使行代表需求维度，列代表轮次分组
round_groups = grouped_data['轮次'].values

# 绘制热力图
fig, ax = plt.subplots()
im = ax.imshow(heatmap_data, cmap='YlGnBu', alpha=0.7)  # 使用 'YlGnBu' 色彩映射，alpha 设置透明度

# 添加颜色条
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('提问需求总值', rotation=-90, va="bottom")

# 设置坐标轴
ax.set_xticks(np.arange(len(round_groups)))
ax.set_yticks([0, 1, 2])  # 对应三个维度
ax.set_xticklabels(round_groups)
ax.set_yticklabels(['生成创作', '获取信息', '内容改进'])
ax.set_xlabel('轮次分组')
ax.set_title('不同轮次分组的提问需求维度偏向性热力图')

# 添加数值标签
for i in range(len(heatmap_data)):
    for j in range(len(round_groups)):
        text = ax.text(j, i, heatmap_data[i, j], ha='center', va='center', color='black')

plt.tight_layout()
plt.show()