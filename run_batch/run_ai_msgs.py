import airsheet
import traceback
from utils.gateway_api_v2_stream import GateWayAPI
from concurrent.futures import ThreadPoolExecutor
import traceback
from run_batch.run_ai import RunAi
import copy

class RunAiMsgs(RunAi):
    def __init__(self,file_id,sheetname,must_have_columns,skip_col_name,clo_num_to_write,max_workers = 6,wps_sid = None):
        super().__init__(file_id,sheetname,must_have_columns,skip_col_name,clo_num_to_write,max_workers,wps_sid)
        self.messages = []
                
    def run_one(self,row):
        try:
            model,system_setting,llm_arguments,version = self.row_to_model_info(row)
            msgs = self.row_to_prompt(row)            
            success,result,response = self.api.chat_msgs(model=model, messages=msgs, context=system_setting, llm_arguments=llm_arguments,version=version,sec_text=self.sec_text)
            airsheet.write_xl([result], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        except Exception as e:
            print(traceback.format_exception(e))
    
    def row_to_prompt(self,row):
        msgs = copy.deepcopy(self.messages)
        for message in msgs:
            for k,v in self.prompt_param_colname_map.items():
                message["content"] = message["content"].replace("{^"+k+"^}", str(row[v]))
        return msgs
        
    
        