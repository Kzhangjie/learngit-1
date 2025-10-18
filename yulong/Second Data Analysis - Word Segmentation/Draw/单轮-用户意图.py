import pandas as pd
import matplotlib.pyplot as plt

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以根据需要选择其他中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-单.xlsx'

# 读取Excel文件
df_filtered = pd.read_excel(excel_file)


# 统计各用户意图的数量
user_intent_counts = df_filtered['用户意图'].value_counts()

# 绘制饼图
fig, ax = plt.subplots(figsize=(10, 8))

# 计算百分比
sizes = user_intent_counts.values
percentages = 100 * sizes / sizes.sum()

# 组合标签和数值
labels_with_values = [f'{label} ({size}次, {percentage:.1f}%)' for label, size, percentage in zip(user_intent_counts.index, sizes, percentages)]

# 绘制饼图
wedges, texts = ax.pie(sizes, startangle=140, labels=labels_with_values)

plt.title('用户意图比例分析', fontsize=16)
plt.tight_layout()

# 添加图例
plt.legend(title='用户意图', loc='upper right')

plt.show()

# 输出用户意图统计信息
print("各用户意图的数量：")
print(user_intent_counts)