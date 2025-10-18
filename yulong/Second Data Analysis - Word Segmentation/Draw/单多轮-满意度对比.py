import matplotlib.pyplot as plt
import numpy as np

# 加载中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 满意度刻度
x_labels = ['0.0', '20.0', '25.0', '30.0', '35.0', '40.0', '45.0', '50.0',
            '55.0', '60.0', '65.0', '70.0', '75.0', '80.0', '85.0', '90.0', '95.0']
x = np.arange(len(x_labels))  # 横坐标索引

# 单轮数据（补充0.0和25.0为0）
single = [0, 6, 0, 20, 22, 74, 137, 760,
          134, 150, 45, 486, 913, 1041, 5362, 4, 6]

# 多轮数据
multi = [10, 298, 39, 748, 470, 885, 777, 2222,
         227, 209, 120, 484, 834, 820, 5914, 4, 7]

# 计算百分比
total_single = sum(single)
total_multi = sum(multi)
single_percent = [s / total_single * 100 for s in single]
multi_percent = [m / total_multi * 100 for m in multi]

width = 0.35  # 柱子宽度

fig, ax = plt.subplots(figsize=(15, 8))
rects1 = ax.bar(x - width/2, single_percent, width, label='单轮')
rects2 = ax.bar(x + width/2, multi_percent, width, label='多轮')

# 添加标签、标题和图例
ax.set_xlabel('满意度')
ax.set_ylabel('百分比 (%)')
ax.set_title('单轮vs多轮满意度分布分组柱状图')
ax.set_xticks(x)
ax.set_xticklabels(x_labels, rotation=45)
ax.legend()

# 标注百分比数值
def autolabel(rects):
    """在每个柱子上方标注百分比数值"""
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',  # 保留一位小数
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=8)

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()
plt.show()    