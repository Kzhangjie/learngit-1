import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Microsoft YaHei'  # 设置字体为楷体

# 读取Excel文件
file_path = r'C:\Users\wps\Desktop\111\数据分析\合并后的分析结果1.xlsx'
df = pd.read_excel(file_path)

# 去除列名为"pc_copilot"的数据
df = df[df['数据来源'] != 'pc_copilot']

# 按“数据来源”和“session id”分组，计算每个session id的总轮次
session_counts = df.groupby(['数据来源', 'session id']).size().reset_index(name='总轮次')

# 统计每个数据来源下不同总轮次的出现次数
session_stats = session_counts.groupby(['数据来源', '总轮次']).size().unstack(fill_value=0)

# 计算每个入口的总轮次分布百分比
data_sources = session_stats.index.tolist()
total_rounds = session_stats.columns.tolist()

# 创建一个包含子图的图形
fig = plt.figure(figsize=(15, 5))  # 创建一个空白图，宽度增加
colors = ['#FFCCCC',  '#CCCCFF', '#CC99FF', '#FF9999', '#FFFFCC', '#CCCCCC']

# 定义布局位置，设置为一行多个
grid = plt.GridSpec(1, len(data_sources), wspace=1)  # wspace设置每个饼图之间的宽度间隔

# 为每个入口创建饼图
for idx, data_source in enumerate(data_sources):
    row = session_stats.loc[data_source]
    sizes = row.values
    labels = [f'总轮次 {tr}' for tr in total_rounds]
    
    # 过滤掉值为0的项
    non_zero_indices = sizes > 0
    sizes = sizes[non_zero_indices]
    labels = [label for label, has_value in zip(labels, non_zero_indices) if has_value]
    
    # 创建子图
    ax = fig.add_subplot(grid[0, idx])
    
    # 绘制饼图并设置半径
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors[:len(sizes)], 
                                     autopct='%1.1f%%', startangle=140, radius=1.4)  # 设置饼图半径
    
    # 设置标题
    ax.set_title(f'{data_source} - 提问总轮次分布')

    # 设置标题，增加pad参数来调整标题与图表的距离
    ax.set_title(f'{data_source} - 提问总轮次分布', pad=30)  # pad参数
    
    # 设置文本样式
    for text in texts + autotexts:
        text.set_fontsize(8)
        text.set_fontfamily('Microsoft YaHei')

# 添加整体标题
fig.suptitle('不同入口下提问总轮次分布饼图', fontsize=16, y=0.9)


plt.show()