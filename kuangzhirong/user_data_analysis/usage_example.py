"""
使用示例：如何使用重构后的WPS Copilot数据分析工具
"""

from utils.user_data_retactor import Config, DataProcessor, FileManager, ETAgentFilter, CSVProcessor

def example_basic_usage():
    """基本使用示例"""
    # 1. 创建配置
    config = Config(
        file_directory=r"D:\your\data\directory",
        wps_sid="your_wps_sid",
        file_id="your_file_id"
    )
    
    # 2. 创建处理器并处理整个目录
    processor = DataProcessor(config)
    success = processor.process_directory()
    
    if success:
        print("处理完成!")
    else:
        print("处理失败!")


def example_custom_filter():
    """自定义过滤器示例"""
    from utils.user_data_retactor import DataFilter
    import pandas as pd
    
    class CustomFilter(DataFilter):
        """自定义过滤器：只处理包含特定关键词的数据"""
        
        def __init__(self, keyword: str):
            self.keyword = keyword
        
        def filter(self, df: pd.DataFrame) -> pd.DataFrame:
            filtered_session_ids = df[
                (df['Role'] == 'user') & 
                (df['Content'].str.contains(self.keyword, na=False))
            ]['SessionID']
            return df[df['SessionID'].isin(filtered_session_ids)]
    
    # 使用自定义过滤器
    config = Config()
    custom_filter = CustomFilter("ppt")  # 只处理包含"ppt"的会话
    csv_processor = CSVProcessor(config, custom_filter)
    
    # 处理单个文件
    success = csv_processor.process("path/to/your/file.csv")


def example_file_operations():
    """文件操作示例"""
    config = Config()
    file_manager = FileManager(config)
    
    # 只解压文件
    file_manager.decompress_gz_files("your/directory")
    
    # 只合并Excel文件
    file_manager.merge_xlsx_files("your/directory", "custom_merged.xlsx")


if __name__ == "__main__":
    # 运行基本示例
    example_basic_usage()
