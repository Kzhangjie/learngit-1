from renfangchao.cc_server.run_log import RunLog

file_id = "ctI6Ti36VX9x"  # 文件
sheetname = "wry-temp"
输出列名 = "planner1"  # 表示会跳过"答案"列已经有内容的行。

输出列编号 = ["AA", "AF", "AP"]  # 表示从把答案写到B列

if __name__ == "__main__":
    cc = RunLog(
        file_id=file_id,
        sheetname=sheetname,
        skip_col_name=输出列名,
        clo_num_to_write=输出列编号,
        env="wry-temp",
    )
    cc.run()
