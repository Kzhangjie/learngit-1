# 生成答案

使用 chat 等目录下面的 gen_xxx 文件生成答案。

也可以用其他代码，只要最后汇总成符合格式的格式即可。

文件格式参考 https://365.kdocs.cn/l/cc8qH3Onudyw

# 生成两两对比

修改并运行 gen_judge_pair.py

```python
file_id = "cibf5tNIvGp4"
# 如果评判到一半，需要新增用例，可以新增一个场景，保持顺序
from_sheets = ["搜索总结1", "搜索总结"]
to_sheet = "盲评记录"
# 模型名，需要是列名的一部分
answer_cols = ["doubao", "r1"]
```

# 启动 streamlit

根目录下执行下面命令,需要修改端口号和文件链接

```bat
streamlit run d:\projects\llm_batch_test\mangping\app.py  --server.headless true --server.port 1850X https://365.kdocs.cn/l/cibf5tNIvGp4
```

# 人工评测

摇人

# 生成分数

生成 elo_score.py

# 其他

表格新增数据后，不需要重启服务，用户名输入`lingxi_reload`，点击`评测下一题`即可。

streamlit run d:\projects\llm_batch_test\mangping\app2.py --server.headless true --server.port 18503 https://365.kdocs.cn/l/cm9nJhMgAslu
