import sys
import json
import airsheet
import os
import traceback
import time
import asyncio
import pandas as pd 
import numpy as np
from run_batch.as_utils import get_df

        
file_id = "cjYW3aNruLB8"
from_sheet = "一对多_FROM"
to_sheet = "一对多_TO"
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
explodes = {
    "模型": ['GLM-4', 'ERNIE-Bot','ERNIE-Bot4'],
    "答案序号":[1,2]
}

if __name__ == '__main__':
    df = get_df(file_id=file_id, sheet_name=from_sheet,wps_sid=WPS_SID)
    for k,v in explodes.items():
        df[k] = [v] * len(df)
        df = df.explode([k],ignore_index=True).reset_index(drop=True)    
    airsheet.write_xl(df, f"A1", sheet_name=to_sheet)