import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 加载中文字体，确保中文能正确显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以根据需要选择其他中文字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 读取表格
excel_file = r'C:\Users\wps\Desktop\111\数据分析\第二次数据分析_划词\画图分析\合并后的总表-单.xlsx'

# 读取Excel文件
df= pd.read_excel(excel_file)

# 数据预处理：确保满意度列是数值类型
df['满意度'] = pd.to_numeric(df['满意度'], errors='coerce')

# 剔除无效的满意度值
df_valid = df.dropna(subset=['满意度'])

# 统计各满意度的数量
satisfaction_counts = df_valid['满意度'].value_counts().sort_index()

# 绘制柱状图
plt.figure(figsize=(12, 8))
satisfaction_counts.plot(kind='bar', color='skyblue', edgecolor='black')

plt.title('满意度分布柱状图', fontsize=16)
plt.xlabel('满意度', fontsize=12)
plt.ylabel('出现次数', fontsize=12)
plt.xticks(rotation=45, ha='right')  # 旋转X轴标签，避免重叠
plt.tight_layout()

# 显示柱状图上的数值
for p in plt.gca().patches:
    plt.gca().annotate(f'{p.get_height():.0f}', 
                       (p.get_x() + p.get_width() / 2., p.get_height()), 
                       ha='center', va='center', 
                       xytext=(0, 9), 
                       textcoords='offset points')

plt.show()

# 输出满意度统计信息
print("各满意度的数量：")
print(satisfaction_counts)