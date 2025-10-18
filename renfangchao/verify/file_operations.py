import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
wps_sid = os.environ.get("WPS_SID", "")


class KDocsFileManager:

    def __init__(
        self,
        base_url="https://365.kdocs.cn",
        wps_sid=wps_sid,
    ):
        self.base_url = base_url
        self.csrf_token = "djWp8miCmJZy6yrEdB8ABMHd72caSrB6"
        self.headers = {
            "sec-ch-ua-platform": '"Windows"',
            "Referer": "https://365.kdocs.cn/ent/41000207/2272442308/435791647412?count=60",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "Content-Type": "application/json",
            "sec-ch-ua-mobile": "?0",
            "Cookie": f"wps_endcloud=1; Hm_lvt_cb2fa0997df4ff8e739c666ee2487fd9=1736934680; coa_id=0; wps_sid={wps_sid}; _ku=1; cid=41000207; uid=1388383710; csrf={self.csrf_token}; swi_acc_redirect_limit=0; exp=259200; wpsua=V1BTVUEvMS4wICh3ZWIta2RvY3M6Q2hyb21lXzEzOC4wLjAuMDsgd2luZG93czpXaW5kb3dzIDEwLjA7IFplQXozbkJXU2VlNng3bTVEYkxsZUE9PTpRMmh5YjIxbElDQXhNemd1TUM0d0xqQT0pIENocm9tZS8xMzguMC4wLjA=; appcdn=volcengine-kdocs-cache.wpscdn.cn; kso_sid=TKS-f0T3DNH8fx7YCDnS0poTTKS7fKoAKQKSflyDrKfng7oUTNFdpJY6SIEFxpR70ebuYCppbfoyIeopTpQXhQODz-EiXRNBIA03GfaUmnKnJpIJRf0pR90pRfauQOOjVo1I-KN_Krr0.STaOznifNFqBftVm7OTn8JGVRB8rMvLy6bQ8XRavY2EP0Eq3YlffEbPb4yf6qD-6MGiXiUyYR7eiPFPWQCsSeQ; nexp=129600",
        }

    def copy_file(self, group_id, file_ids, target_parent_id):
        """复制文件到指定目录"""
        url = f"{self.base_url}/3rd/drive/api/v3/groups/{group_id}/files/batch/copy"
        data = {
            "fileids": file_ids,
            "groupid": group_id,
            "target_groupid": group_id,
            "target_parentid": target_parent_id,
            "duplicated_name_model": 0,
            "csrfmiddlewaretoken": self.csrf_token,
        }

        print(f"请求URL: {url}, 请求数据: {data}")

        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def rename_file(self, group_id, file_id, new_name):
        """重命名文件"""
        url = f"{self.base_url}/3rd/drive/api/v3/groups/{group_id}/files/{file_id}"
        data = {"fname": new_name, "csrfmiddlewaretoken": self.csrf_token}

        response = requests.put(url, headers=self.headers, json=data)
        return response.json()

    def query_files(self, group_id, parent_id, count=20):
        """查询文件列表"""
        url = f"{self.base_url}/3rd/drive/api/v5/groups/{group_id}/files"
        params = {
            "include": "acl,pic_thumbnail",
            "parentid": parent_id,
            "with_link": "true",
            "review_pic_thumbnail": "true",
            "with_sharefolder_type": "true",
            "offset": 0,
            "count": count,
            "order": "desc",
            "orderby": "mtime",
            "exclude_exts": "",
            "include_exts": "",
        }

        headers = self.headers.copy()
        headers.pop("Content-Type")  # GET请求不需要Content-Type

        response = requests.get(url, headers=headers, params=params)
        return response.json()

    def generate_filename_with_date(
        self, is_test, base_name="接口验证", extension=".xlsx"
    ):
        """生成带日期的文件名"""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M")
        env = "测试环境" if is_test else "正式环境"
        return f"{base_name}_{env}_{date_str}{extension}"

    def copy_rename_and_query(
        self,
        group_id=2272442308,
        file_ids=[437224990302],
        target_parent_id=435791647412,
        is_test=True,
    ):
        """完整的复制、重命名、查询流程"""
        try:
            # 1. 复制文件
            print("正在复制文件...")
            copy_result = self.copy_file(group_id, file_ids, target_parent_id)
            print(f"复制结果: {copy_result}")

            if copy_result.get("result") != "ok":
                return None

            new_file_ids = copy_result.get("fileids", [])
            if not new_file_ids:
                return None

            new_file_id = new_file_ids[0]

            # 2. 重命名文件
            print("正在重命名文件...")
            new_filename = self.generate_filename_with_date(is_test)
            rename_result = self.rename_file(group_id, new_file_id, new_filename)
            print(f"重命名结果: 文件名已改为 {new_filename}")

            # 3. 查询文件列表获取link_id
            print("正在查询文件信息...")
            query_result = self.query_files(group_id, target_parent_id)

            # 查找新创建的文件
            for file_info in query_result.get("files", []):
                if file_info["id"] == new_file_id:
                    link_id = file_info.get("link_id")
                    print(f"文件创建成功! Link ID: {link_id}")
                    return {
                        "file_id": new_file_id,
                        "filename": new_filename,
                        "link_id": link_id,
                        "link_url": file_info.get("link_url"),
                    }

            return None

        except Exception as e:
            print(f"操作失败: {str(e)}")
            return None


def copy_file(is_test):
    """主函数 - 执行文件复制重命名操作"""
    manager = KDocsFileManager()

    # 输入参数
    group_id = 2272442308

    file_ids = [437224990302] if is_test else [435791656799]
    target_parent_id = 435791647412

    print(f"开始处理文件复制操作...")
    print(f"Group ID: {group_id}")
    print(f"File IDs: {file_ids}")
    print(f"Target Parent ID: {target_parent_id}")

    result = manager.copy_rename_and_query(
        group_id, file_ids, target_parent_id, is_test
    )

    if result:
        print("\n操作完成!")
        print(f"新文件ID: {result['file_id']}")
        print(f"新文件名: {result['filename']}")
        print(f"Link ID: {result['link_id']}")
        print(f"Link URL: {result['link_url']}")
    else:
        print("操作失败!")
    return result


if __name__ == "__main__":
    main()
