from dotenv import load_dotenv

load_dotenv()

import logging
import os
from urllib.parse import unquote

import requests
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
ip_blacklist = [
    "10.23.14.60",
    "10.13.156.236",
    "10.13.70.92",
    "10.13.144.13",
    "10.13.88.141",
    "10.13.138.117",
    "10.13.138.55",
]


def get_remote_ip() -> str:
    """Get remote ip."""

    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip


def get_all_cookies():
    """
    WARNING: This uses unsupported feature of Streamlit
    Returns the cookies as a dictionary of kv pairs
    """
    from streamlit.web.server.websocket_headers import _get_websocket_headers

    headers = _get_websocket_headers()
    if headers is None:
        return {}

    if "Cookie" not in headers:
        return {}

    cookie_string = headers["Cookie"]
    cookie_kv_pairs = cookie_string.split(";")

    cookie_dict = {}
    for kv in cookie_kv_pairs:
        k_and_v = kv.split("=")
        k = k_and_v[0].strip()
        v = k_and_v[1].strip()
        cookie_dict[k] = unquote(v)
    return cookie_dict


import streamlit as st


@st.cache_data
def auth(wps_sid):
    return requests.get(
        "http://api.wps.cn/v7/users/current",
        cookies={"wps_sid": wps_sid},
    ).json()


admins = ["任方超"]
user_ip_dict = {
    "10.13.155.168": "任方超",
    "::1": "任方超",
    "10.13.242.222": "朱保怡",
    "10.23.197.56": "邱晓娜",
    "10.13.230.79": "王芳",
    "10.13.158.121": "匡志荣",
}


def authorize() -> int:
    # ip_users_str = os.getenv("IP_USERS","")
    # user_ip_dict = {}
    # for item in ip_users_str.split(","):
    #     try:
    #         ip, name = item.split(":",1)
    #         user_ip_dict[ip] = name
    #     except ValueError:
    #         logging.info(f"无法解析的项: {item}")
    ip = get_remote_ip()
    st.session_state.ip = ip
    if ip in ip_blacklist:
        st.error(str("无权限"))
        st.stop()
    # cookies = get_all_cookies()
    # wps_sid = cookies.get("wps_sid","")
    # if wps_sid:
    #     rs = auth(wps_sid)
    #     if rs["code"] == 0:
    #         try:
    #             uid = rs["data"]["id"]
    #             username = rs["data"]["user_name"]
    #             authorized_users = os.getenv("AUTHORIZED_UIDS", "").split(",")
    #             authorized_users = [o for o in authorized_users if o]
    #             admin_users = os.getenv("ADMIN_UIDS", "").split(",")
    #             admin_users = [o for o in admin_users if o]
    #             isvaild = uid in authorized_users
    #             is_admin = uid in admin_users
    #             if isvaild:
    #                 logging.info(f'根据cookie鉴权通过,请求ip:{ip} {username}')
    #                 return True,username,is_admin
    #             else:
    #                 logging.warning(f'根据cookie鉴权拒绝,请求ip:{ip} {username}')
    #         except Exception as e:
    #             logging.info('请求ip:',ip,"未授权用户")
    username = user_ip_dict.get(ip)
    if username:
        logging.info(f"根据ip鉴权通过,请求ip:{ip} {username}")
        st.session_state.username = username
        return True, username, username in admins
    else:
        logging.warning(f"根据ip鉴权拒绝,请求ip被拦截:{ip}")
        st.error(f"无权限,发送{ip}给任方超增加白名单")
        st.stop()
