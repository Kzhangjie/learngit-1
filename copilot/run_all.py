#串行运行所有脚本：生成调度结果+校验断言

#gen_model_answer-qxn.py   更改用例文件fid+模型版本（model_url用外网、cc用内网url）
#judge_function.py    更改用例文件fid
# parse_answer.py    更改用例文件fid
# judge_function_docs.py    更改用例文件fid

import subprocess
import os

def run_script(script_path):
    try:
        result = subprocess.run(['python', script_path], check=True, text=True, capture_output=True)
        print(f"Output of {os.path.basename(script_path)}:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running {os.path.basename(script_path)}:")
        print(e.stderr)

if __name__ == '__main__':
    root_directory = './copilot/'
    # scripts = ['gen_model_answer-qxn.py', 'judge_function.py' ,'parse_answer.py','judge_function-docs.py']
    scripts = ['gen_model_answer-qxn.py', 'judge_function.py' ]
    # scripts = [ 'judge_function.py' ,'parse_answer.py','judge_function-docs.py']
    # scripts = ['parse_answer.py','judge_function-docs.py']
    for script in scripts:
        script_path = os.path.join(root_directory, script)
        run_script(script_path)