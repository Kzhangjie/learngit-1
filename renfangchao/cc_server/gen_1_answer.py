from renfangchao.cc_server.run_cc import RunCC

file_id = "cmmCbqhoPJ7M"  # 文件
sheetname = "测试"
输出列名 = "resp_session_id"  # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "N"  # 表示从把答案写到B列

if __name__ == "__main__":
    cc = RunCC(
        file_id=file_id,
        sheetname=sheetname,
        skip_col_name=输出列名,
        clo_num_to_write=输出列编号,
        is_test=True,
        max_workers=4,
        custom_headers={"X-Cc-Region": "feat_ai_image"},
    )
    cc.run()
