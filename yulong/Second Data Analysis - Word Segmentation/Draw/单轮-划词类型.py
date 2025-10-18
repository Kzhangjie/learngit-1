import pandas as pd
import matplotlib.pyplot as plt

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以根据需要选择其他中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-单.xlsx'

# 读取Excel文件
df = pd.read_excel(excel_file)

# 统计各划词类型的数量
wording_type_counts = df['划词类型'].value_counts()

# 绘制饼图
fig, ax = plt.subplots(figsize=(10, 8))

# 计算百分比
sizes = wording_type_counts.values
percentages = 100 * sizes / sizes.sum()

# 组合标签和数值
labels_with_values = [f'{label} ({size}次, {percentage:.1f}%)' for label, size, percentage in zip(wording_type_counts.index, sizes, percentages)]

# 绘制饼图
wedges, texts = ax.pie(sizes, startangle=140, labels=labels_with_values)

plt.title('划词类型比例分析', fontsize=16)
plt.tight_layout()

# 添加图例
plt.legend(title='划词类型', loc='upper right')

plt.show()

# 输出划词类型统计信息
print("各划词类型的数量：")
print(wording_type_counts)