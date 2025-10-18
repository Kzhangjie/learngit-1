import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 读取Excel文件
file_path = r'C:\Users\wps\Desktop\111\数据可视化\正式\合并后的分析结果1.xlsx'
df = pd.read_excel(file_path)

# 筛选出 生成创作、获取信息、内容改进 列值为 是/否 的数据
valid_values = ['是', '否']
df = df[df['生成创作'].isin(valid_values) & df['获取信息'].isin(valid_values) & df['内容改进'].isin(valid_values)]

# 设置字体为楷体
plt.rcParams['font.family'] = 'KaiTi'

# 构建转移字典
transfer_dict = {}
for index, row in df.iterrows():
    session_id = row['session id']
    turn = row['轮次']
    # 当前轮次的需求维度
    current_generate = row['生成创作']
    current_acquire = row['获取信息']
    current_improve = row['内容改进']
    # 构建当前轮次需求维度的元组
    current_key = (current_generate, current_acquire, current_improve)

    # 查找下一个轮次的行
    next_row = df[(df['session id'] == session_id) & (df['轮次'] == turn + 1)]
    if not next_row.empty:
        next_generate = next_row['生成创作'].values[0]
        next_acquire = next_row['获取信息'].values[0]
        next_improve = next_row['内容改进'].values[0]
        next_key = (next_generate, next_acquire, next_improve)
        # 更新转移字典
        if current_key not in transfer_dict:
            transfer_dict[current_key] = {}
        if next_key not in transfer_dict[current_key]:
            transfer_dict[current_key][next_key] = 0
        transfer_dict[current_key][next_key] += 1

# 定义转换函数
def tuple_to_text(tup):
    parts = []
    if tup[0] == '是':
        parts.append('生成创作')
    if tup[1] == '是':
        parts.append('获取信息')
    if tup[2] == '是':
        parts.append('内容改进')
    return '＋'.join(parts) if parts else '无'

# 转换状态表示
states = list(set([key for keys in transfer_dict.values() for key in keys.keys()]))
states_text = [tuple_to_text(state) for state in states]
state_to_index = {state: i for i, state in enumerate(states)}

# 定义期望的顺序
desired_order = [
    '生成创作', '获取信息', '内容改进',
    '生成创作＋获取信息', '生成创作＋内容改进',
    '获取信息＋内容改进', '无'
]

# 筛选出实际存在的状态，并按期望顺序排列
actual_states = [state for state in desired_order if state in states_text]
actual_state_tuples = [states[states_text.index(state)] for state in actual_states]
new_state_to_index = {state: i for i, state in enumerate(actual_state_tuples)}

# 构建新的转移矩阵
transition_matrix = np.zeros((len(actual_states), len(actual_states)))
for current_state, next_states in transfer_dict.items():
    if current_state in actual_state_tuples:
        current_index = new_state_to_index[current_state]
        total = sum(next_states.values())
        for next_state, count in next_states.items():
            if next_state in actual_state_tuples:
                next_index = new_state_to_index[next_state]
                transition_matrix[current_index][next_index] = count / total

# 绘制热力图
plt.figure(figsize=(12, 8))
sns.heatmap(transition_matrix, annot=True, fmt=".2f", cmap="YlGnBu",
            xticklabels=actual_states,
            yticklabels=actual_states)
plt.xlabel("下一轮需求维度")
plt.ylabel("当前轮需求维度")
plt.title("需求维度转移概率热力图")
plt.tight_layout()
plt.show()

# 绘制多折线图，展示每个状态转移到其他状态的概率
for i in range(len(actual_states)):
    plt.plot(range(len(actual_states)), transition_matrix[i], marker='o', label=f"From {actual_states[i]}")

plt.xlabel("下一轮需求维度")
plt.ylabel("转移概率")
plt.title("需求维度转移概率折线图")
plt.xticks(range(len(actual_states)), actual_states, rotation=45)
plt.legend()
plt.tight_layout()
plt.show()