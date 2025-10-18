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

# 按用户意图和轮次分组并计数
grouped = df.groupby(['用户意图', '轮次']).size().unstack(fill_value=0)

# 绘制热力图
plt.figure(figsize=(12, 10))
sns.heatmap(grouped, annot=True, fmt="d", cmap='YlGnBu', linewidths=0.5)

plt.title('用户意图与当前轮的关联度热力图', fontsize=16)
plt.xlabel('轮次', fontsize=14)
plt.ylabel('用户意图', fontsize=14)
plt.tight_layout()
plt.show()