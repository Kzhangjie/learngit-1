# 安装依赖

`pip install -r requirements.txt`

# 添加本目录到 PYTHONPATH

可以参考https://www.cnblogs.com/willowj/p/6433103.html，给环境变量`PYTHONPATH` 增加此代码根目录

# 添加环境变量

在此代码根目录增加.env 文件，内容为

```
AI_GATEWAY_TOKEN_V2=xxxx
AI_GATEWAY_PRODUCT_NAME_V2=xxxx
AI_GATEWAY_UID_V2=xxxx
AI_GATEWAY_INTENTION_CODE_V2=xxxx
WPS_SID=xxxx
```

其中 `WPS_SID` 为自己的 `WPS_SID`,可以在https://365.kdocs.cn/ 网页打开开发者工具获取，用于读写在线文档

`AI_GATEWAY_*` 为 AI 网关的相关配置，请向相关开发获取或申请

# 增加网关 host

```
120.92.124.158 aigc-gateway-test.ksord.com
172.16.53.133 ai-gateway-dev.ksord.com
159.138.103.150 aigc-gateway-sg-test.ksord.com
```

# 运行

`python .\example\run_ai_单个模型_模板.py`

# KPP 相关操作，参考 https://365.kdocs.cn/l/cfPz3cUx1vyW

# 示例说明

本指南提供了在不同场景下使用单个或多个模型批量跑 Prompt 的方法，包括预处理、结果处理和输入处理的详细步骤。

## 0. 文档权限

由于数据都写在在线表格中，请给任方超该表格文档的编辑权限。如果不想给，请参考示例传入自己的 WPS_SID。

## 1. 单个模型

- 参考 [run*ai*单个模型\_模板.py](./example/run_ai_单个模型_模板.py)

## 2. 预处理

### 2.1 参数处理

批量跑 Prompt 接受的参数格式为每列 1 个。如果不符合，请使用代码处理。

- 参考 [代码处理示例\_拆分参数.py](./example/代码处理示例_拆分参数.py)
  1. 先定义一个通用的`func`方法，调试通过。
  2. 在`run_one`中调用`func`方法。

### 2.2 测试不同模型

若需要针对一批 case 跑不同模型或不同次数，需将一行数据变为多行数据。

- 参考 [one_to_muilt.py](./example/one_to_muilt.py)

## 3. 结果处理

### 3.1 GPT4 评分

等价于单个模型跑 Prompt 的方法。

### 3.2 代码处理结果

与参数处理相同，均通过代码处理。

- 参考 [代码处理示例\_校验 json.py](./example/代码处理示例_校验json.py)

校验 json 的需求较为通用，相应的功能已集成至(./run_batch/code_utils/validate_json_in_text.py)。在代码处理示例中，使用以下导入方式：

```python
from run_batch.code_utils.validate_json_in_text import func
```

## 4. 多轮对话

### 第一轮

和单轮对话一样，不过增加一步把 msgs 写入表格，以便后续使用

参考[run*ai*二轮对话\_1st.py](./example/run_ai_二轮对话_1st.py)

### 第一轮后处理（可选）

只有解析第一轮的结果为第二轮的参数，才需要这一步。否则不需要。

参考[run*ai*二轮对话\_1st_parse.py](./example/run_ai_二轮对话_1st_parse.py)

示例中将第一轮的结果写入"解析 param_d"列，作为第二轮的参数

### 第二轮

和单轮对话一样，不过要获取第一轮的 msgs,调用 chat_msgs 接口。

参考[run*ai*二轮对话\_2nd.py](./example/run_ai_二轮对话_2nd.py)

### 更多轮

如果需要第三轮，则第二轮需要把 msgs 写入表格，以便后续使用，依次类推。
