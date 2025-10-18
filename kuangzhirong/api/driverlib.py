from requests import Request, Response, Session, RequestException, get


def get_link_id(url: str) -> str:
    idx = url.rfind("?")
    if idx != -1:
        url = url[:idx]

    idx = url.rfind("/")
    if idx != -1:
        link_id = url[idx + 1:]
        if link_id:
            return link_id
        else:
            url = url[:idx]
    else:
        return ""


def get_special_group(wps_sid: str) -> int:
    """
    获取"我的云文档"分组ID
    """
    rsp = get(
        "https://365.kdocs.cn/3rd/drive/api/v3/groups/special",
        headers={
            "Content-Type": "application/json",
            "Cookie": f"wps_sid={wps_sid}",
        },
    )
    if rsp.status_code != 200:
        raise Exception(f"get_special_group error: invalid status {rsp.status_code}")
    # 返回group_id即可
    return int(rsp.json().get("id"))


def print_request_header_body(describe: str, request: Request):
    import pprint

    print("\n\n----%s request header start----" % describe)
    print("%s %s" % (request.method, request.url))
    pprint.pprint(request.headers)
    print("----%s request header end----" % describe)
    print("----%s request body start----" % describe)
    pprint.pprint(request.data or request.json)
    print("----%s request body end----\n" % describe)


def print_response_header_body(describe: str, response: Response):
    import pprint

    print("\n----%s response header start----" % describe)
    pprint.pprint(response.headers)
    print("----%s response header end----" % describe)
    print("----%s response body start----" % describe)
    pprint.pprint(response.text)
    print("----%s response body end----\n\n" % describe)


def parse_fetch_response_args(fetch_response_body_json: dict, upload_response: Response) -> dict:
    """本函数用来说明如何解析 第一步返回值中 response 字段中args_开头的key"""
    param = {}
    # args_key需要单独解析
    args_key_parse = fetch_response_body_json["response"]["args_key"].split(".")
    if args_key_parse[0] == "header":
        param["sha1"] = upload_response.headers.get(args_key_parse[1])
    for k in fetch_response_body_json["response"]:
        if k == "args_key" or k == "expect_code":
            continue
        if k.startswith("args_"):  # 注意整块是args_ 分块是arg_            别喷我，历史原因
            key = k[5:]
            rule = fetch_response_body_json["response"][k].split(".")  # 这里replace是有必要的，金山云的坑, etag值会多返回引号
            if rule[0] == "header":
                param[key] = upload_response.headers.get(rule[1]).replace('"', "")
            elif rule[0] == "body":
                if upload_response.headers.get("content-type") == "application/json":
                    data = upload_response.json()
                    for field in rule[1:]:
                        if not data:
                            break
                        data = data[field]
                    # 这里replace是有必要的，金山云的坑, etag值会多返回引号
                    param[key] = data.replace('"', "")
    return param


def read_file_data(filepath: str) -> tuple[str, int, str, bytes]:
    """
    读取文件数据. 返回: name, size, sha256, data
    """
    import os
    import hashlib

    with open(filepath, "rb") as f:
        data = f.read()

    name = os.path.basename(filepath)
    size = os.path.getsize(filepath)

    h = hashlib.sha256()
    h.update(data)

    return name, size, h.hexdigest(), data


class PrivyDrive(object):
    def __init__(self, wps_sid: str, trace: bool = False, group_id: str = None, parent_id: str = None) -> None:
        self.cookie: str = f"wps_sid={wps_sid};"
        # self.group_id: int = get_special_group(wps_sid)
        self.group_id: int = group_id
        self.parent_id: int = parent_id
        self.session: Session = Session()
        self.TRACE = trace

    def __del__(self):
        if self.session:
            self.session.close()

    def fetch_request(self, name: str, size: int, sha256: str) -> Response:
        request = Request(
            method="PUT",
            url="https://drive.kdocs.cn/api/v5/files/upload/create_update",
            headers={
                "origin": "https://www.kdocs.cn",
                "Content-Type": "application/json",
                "Cookie": self.cookie,
            },
            json={
                "group_id": self.group_id,
                "parent_id": self.parent_id,
                "name": name,
                "size": size,
                "sha256": sha256,
                "req_by_internal": False,
                "with_rapid": True,  # 会返回秒传信息，需要接秒传的，参考秒传接口
                "tried_store": "",  # 如果你想指定上传到ks3时，填ks3sh,ks3gz,obscn,coscq。表明你列出来的存储桶已尝试并失败，云文档不再返回该桶
            },
        )
        if self.TRACE:
            print_request_header_body("第一步: 请求云文档获取文件上传地址等信息", request)

        response = self.session.send(request.prepare())

        if self.TRACE:
            print_response_header_body("第一步: 请求云文档获取文件上传地址等信息", response)

        return response

    def upload_request(self, fetch_upload_info_response_body_json: dict, data: bytes) -> Response:
        request = Request(
            method=fetch_upload_info_response_body_json["method"],
            url=fetch_upload_info_response_body_json["url"],
            headers=fetch_upload_info_response_body_json["request"]["headers"],
            data=data,
        )
        if self.TRACE:
            print_request_header_body("第二步：上传文件到云存储商", request)

        response = self.session.send(request.prepare())

        if self.TRACE:
            print_response_header_body("第二步：上传文件到云存储商", response)

        return response

    def create_request(self, create_file_request_json: dict) -> Response:
        """第三步：创建文件元信息到云文档"""
        request = Request(
            method="POST",
            url="https://drive.kdocs.cn/api/v5/files/file",
            headers={
                "origin": "https://www.kdocs.cn",
                "Content-Type": "application/json",
                "Cookie": self.cookie,
            },
            json=create_file_request_json,
        )
        if self.TRACE:
            print_request_header_body("第三步：创建文件元信息到云文档", request)

        response = self.session.send(request.prepare())

        if self.TRACE:
            print_response_header_body("第三步：创建文件元信息到云文档", response)

        return response

    def upload(self, filepath: str) -> str:
        name, size, hash, data = read_file_data(filepath)

        """上传整块文件"""
        fetch_response = self.fetch_request(name, size, hash)
        if fetch_response.status_code != 200:
            if self.TRACE:
                print("[Fail] 第一步：请求云文档获取文件上传地址等信息 失败。status_code: %d response.body: %s",
                      fetch_response.status_code, fetch_response.content)
            raise RequestException(f"drive upload fetch_request invalid status: {fetch_response.status_code}")

        fetch_response_json = fetch_response.json()
        upload_response = self.upload_request(fetch_response_json, data)
        if upload_response.status_code not in fetch_response_json["response"]["expect_code"]:
            if self.TRACE:
                print("[Fail] 第二步：上传文件到云存储商 失败。status_code: %d response.body: %s",
                      upload_response.status_code, upload_response.content)
            raise RequestException(f"drive upload upload_request invalid status: {upload_response.status_code}")

        create_file_request_json = {
            "groupid": self.group_id,
            "parentid": self.parent_id,
            "name": name,
            "size": size,
            "store": fetch_response.json()["store"],
        }
        params = parse_fetch_response_args(fetch_response_json, upload_response)
        create_file_request_json.update(params)
        create_response = self.create_request(create_file_request_json)
        if create_response.status_code != 200:
            if self.TRACE:
                print("[Fail] 第三步：失败。status_code: %d response.body: %s" % (
                    create_response.status_code, create_response.content))
            raise RequestException(f"drive upload create_request invalid status: {create_response.status_code}")

        return create_response.json().get("link_url")

    def download_by_cid(self, cid: str, dirname: str = "/tmp", filename: str = "") -> str:
        from urllib import parse
        import os

        # 获取与解析download_url
        with get(
                f"https://365.kdocs.cn/api/v3/office/file/{cid}/download?options=%7B%7D&clientId=fa010083029249ba7523d1086de401b1&format=xlsx",
                headers={"Cookie": self.cookie},
        ) as rsp:
            if rsp.status_code != 200:
                raise RequestException(f"get download_url invalid status: {rsp.status_code}")

            download_url = rsp.json().get("download_url")
            if download_url is None:
                raise RequestException("get download_url missing download_url")

            if not filename:
                download_url_obj = parse.urlparse(download_url)
                if download_url_obj is None:
                    raise RequestException("get download_url invalid download_url")

                download_query = parse.parse_qs(download_url_obj.query)
                if download_query is None:
                    raise RequestException("get download_url missing download_url")

                response_content_disposition = download_query.get("response-content-disposition")
                if response_content_disposition is None:
                    raise RequestException("get download_url missing download_url")

                response_content_disposition = parse.unquote(response_content_disposition[0])
                filename = response_content_disposition.removeprefix(r"attachment;filename*=utf-8''")

        # 下载与存储临时文件(注意:必须拼上文件名称及相关类型后缀,否则summary提取报错)
        filepath = os.path.join(dirname, filename)
        os.makedirs(dirname, exist_ok=True)
        with (
            open(filepath, "wb") as out,
            get(
                download_url,
                headers={"Cookie": self.cookie},
                stream=True,
            ) as rsp,
        ):
            if rsp.status_code != 200:
                raise RequestException(f"download invalid status: {rsp.status_code}")

            for chunk in rsp.iter_content(chunk_size=4096):
                out.write(chunk)

        return filepath

    def download(self, link_url: str, dirname: str = "/tmp", filename: str = "") -> str:
        file_id = get_link_id(link_url)
        if not file_id:
            raise ValueError("invalid link_url")
        return self.download_by_cid(file_id, dirname, filename)

# print(PrivyDrive(wps_sid="V02SJ6JlNtB-5Kv2g60VvoUQh9WMbS400aad15be00529bd593").upload("/data/copy-05-test.xlsx"))
# print(PrivyDrive(wps_sid="V02SJ6JlNtB-5Kv2g60VvoUQh9WMbS400aad15be00529bd593").download("https://365.kdocs.cn/l/chJILY2q1lbc", "/tmp", "text.xlsx"))
