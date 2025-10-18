# 折线图：不同时间段下各个总轮次的比例趋势

import pandas as pd
import matplotlib.pyplot as plt

# 读取Excel文件
file_path = r'C:\Users\wps\Desktop\111\数据可视化\正式\合并后的分析结果1.xlsx'
df = pd.read_excel(file_path)

# 统计每个时间段和每个 session id 的出现次数（总轮次）
session_counts = df.groupby(['时间', 'session id']).size().reset_index(name='总轮次')

# 按时间段和总轮次分组并统计出现次数
time_turn_counts = session_counts.groupby(['时间', '总轮次']).size().unstack(fill_value=0)

# 去除总轮次为8的数据
time_turn_counts = time_turn_counts.drop(columns=[8], errors='ignore')

# 计算每个时间段的总轮次数
total_turns_per_time = time_turn_counts.sum(axis=1)

# 计算每个时间段每个总轮次的比例
turn_proportions = time_turn_counts.div(total_turns_per_time, axis=0)

# 设置字体为楷体
plt.rcParams['font.family'] = 'KaiTi'  # 设置为楷体

# 定义每条折线的颜色
colors = ['#CC6699', '#FF6666', '#666699', '#CC6699', '#669933',  '#339999']

# 绘制多折线图
plt.figure(figsize=(10, 6))
for i, turn in enumerate(turn_proportions.columns):
    # 绘制每条折线
    line, = plt.plot(turn_proportions.index, turn_proportions[turn], marker='o', color=colors[i % len(colors)], label=f'总轮次={turn}')
    
    # 获取最大值和最小值的位置和值
    y_values = turn_proportions[turn]
    max_y = y_values.max()
    min_y = y_values.min()
    max_x = y_values.idxmax()
    min_x = y_values.idxmin()
    
    # 添加最大值标签
    plt.text(max_x, max_y + 0.01, f'{max_y:.2%}', ha='center', va='bottom', color=line.get_color(), fontsize=12)
    # 添加最小值标签
    plt.text(min_x, min_y + 0.01, f'{min_y:.2%}', ha='center', va='bottom', color=line.get_color(), fontsize=12)

# 添加标题和标签
plt.title('不同时间段下各个总轮次的比例趋势', fontsize=16)
plt.xlabel('时间段', fontsize=14)
plt.ylabel('比例', fontsize=14)

# 添加图例
plt.legend()

# 自动旋转日期标签，以适应图表宽度
plt.gcf().autofmt_xdate()

# 显示图表
plt.tight_layout()
plt.show()