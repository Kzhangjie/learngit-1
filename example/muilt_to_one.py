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
from_sheet = "多对一_FROM"
to_sheet = "多对一_TO"
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID

if __name__ == '__main__':
    df = get_df(file_id=file_id, sheet_name=from_sheet,wps_sid=WPS_SID)
    df['最高分'] = df.groupby(['用例编号','模型'])['得分'].transform('max')
    df = df[df['得分'] == df['最高分']].drop('得分', axis=1).reset_index(drop=True)  
    print(df)
    airsheet.write_xl(df, f"A1", sheet_name=to_sheet)
