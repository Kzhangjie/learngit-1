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

# 按session_id和轮次排序
df = df.sort_values(['session_id', '轮次'])

# 创建用户意图序列
sessions = df.groupby('session_id')['用户意图'].apply(list).reset_index()

# 创建转移矩阵
from itertools import chain

# 获取所有唯一的用户意图
unique_intents = list(set(chain.from_iterable(sessions['用户意图'])))

# 初始化转移矩阵
transition_matrix = pd.DataFrame(0, index=unique_intents, columns=unique_intents, dtype=float)

# 统计转移次数
for session in sessions['用户意图']:
    for i in range(len(session)-1):
        current_intent = session[i]
        next_intent = session[i+1]
        transition_matrix.at[current_intent, next_intent] += 1

# 计算转移概率
for i in unique_intents:
    total = transition_matrix.loc[i].sum()
    if total > 0:
        transition_matrix.loc[i] = transition_matrix.loc[i] / total

# 绘制热力图
plt.figure(figsize=(12, 10))
sns.heatmap(transition_matrix, annot=True, cmap='YlGnBu', linewidths=0.5)

plt.title('上下轮的用户意图维度关联性热力图', fontsize=16)
plt.xlabel('下一轮用户意图', fontsize=14)
plt.ylabel('当前轮用户意图', fontsize=14)
plt.tight_layout()
plt.show()