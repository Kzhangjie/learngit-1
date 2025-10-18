import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv
import requests

load_dotenv()


DEFAULT_COOKIE_TEMPLATE = (
    "wps_sid={wps_sid}; x-kso-app-name=pc-office; x-kso-app-version=12.9.0.22963; "
    "x-kso-device-code=Fktcavrwci8eSxth4G5jByTMPMKo; "
    "x-kso-device-id=9e84b548704e2efb283931a4ec00748f; "
    "x-kso-device-name=a3NkZAAoRkkzUDZOUSk=; "
    "x-kso-device-security-code=eyJrdHkiOiJFQyIsImNydiI6IlAtMjU2IiwieCI6ImZRSVVad3NVTWdVcW55SnhvZHZfSkh5ZUsxdlRMMjZUZUgyQnpDM0xzTlE9IiwieSI6IkhOOGYwZlJwb2Y2c05Qb2lGcFhwQnk5VS0xenVYaE9EQXg2UE1hbS1nVFU9In0=; "
    "x-kso-device-signature=1760497052:mfhCnjLNJIsr5QNzgQrpg8UvOBJqGb5rpx4MbPYMwRPOs0mzw69Yax_2PBDiG772ZV06Qn4N2iKowRDW4zKZrg==; "
    "x-kso-device-trademark=RGVsbCBJbmMu; x-kso-device-version=Vm9zdHJvIDM3MTA=; "
    "x-kso-platform-type=windows; x-kso-platform-version=10; "
    "wpsua=V1BTVUEvMS4wIChwYy1vZmZpY2U6MTIuOS4wLjIyOTYzOyB3aW5kb3dzOjEwLjAgV09XNjQ7 "
    "9llODRiNTQ4NzA0ZTJlZmIyODM5MzFhNGVjMDA3NDhmOlJFVlRTMVJQVUMxR1NUTlFOazVSKQ==; "
    "kwtid=c46cd4ef; kso_sid=TKS-f0TrZPWlT07zmizH0poTTKI7fKoAKQKSaCYVRr0H6TodTI90xoU0IpNw_8jlsajzdXRFAzrCA7oqRzKwR7NFIQoUrBEUODSThFWujHRsbRrC6LokHnQ-T2KwY21zR2keNfouTKS-IQPA53LvYE1uScKAz90sEedgGCx1f62WtkX8_NBA-8iNLUf_GvekTUrfUpIASKrLSrwxR7D5L9KlR9I5N9N_Krr0.5jTPGI2buHmhJZTiGtGU3Ds-nxTdmYXOXI9LDuqs-RazJ-AJ51Jyx898jI4vO5PZEbn2DnqLFPqCg7ax1YoTkK; "
    "cid=0; uid=280076424; cv=t_jku0GNhCgMkKDqHdq-RBP4qO6b1ZWzglMiCvZu2ERPgw9QRMk9LWzsGcV_4NoUpKMxqxjc.7npUHIXbWTK; "
    "_ku=1; coa_id=0; wps_endcloud=1; swi_acc_redirect_limit=0; "
    "weboffice_device_id=32f6481e2bcf45087b8d29796175244a; visitorid=764390733; "
    "weboffice_cdn=1; region=t_release_istio; csrf=HkYy7mPBzwFYbRpPip7kX6Y3mCDwbJNE; lang=zh-CN"
)


@dataclass(frozen=True)
class KDocsCredentials:
    wps_sid: str

    @classmethod
    def from_env(cls, env_key: str = "WPS_SID") -> "KDocsCredentials":
        # value = os.environ.get(env_key)
        value = "V02Sf9YTKj37P5mxJEgaS8RJ9uvjUmk00a481a4b00110778d3"
        if not value:
            raise RuntimeError(f"缺少环境变量 {env_key}")
        return cls(wps_sid=value)


@dataclass(frozen=True)
class KDocsEndpoints:
    # base_url: str = "https://www.kdocs.cn/api/aigc/v3/analysis"
    base_url: str = "https://10.13.34.11/api/aigc/v3/analysis"

    @property
    def sessions(self) -> str:
        return f"{self.base_url}/sessions"

    def completions(self, session_id: str) -> str:
        return f"{self.base_url}/sessions/{session_id}/completions"


@dataclass
class KDocsCookieBuilder:
    credentials: KDocsCredentials
    template: str = DEFAULT_COOKIE_TEMPLATE

    def build(self) -> str:
        return self.template.format(wps_sid=self.credentials.wps_sid)


class KDocsHeadersBuilder:
    _shared_headers: Dict[str, str] = {
        "Host": "www.kdocs.cn",
        "aigc-gateway-intention-code": "kdocs_airsheet_analysis_send",
        "aigc-gateway-product-name": "kdocs-as-baseserver",
        "aigc-gateway-sectext-from": "AI_DRIVE_AS",
        "aigc-gateway-sectext-scene": "analysis_assistant",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/104.0.5112.102 Safari/537.36 WpsOfficeApp/12.9.0.22963 (per_plus,windows) "
        "WPSKdocsHybrid/1.0 PreloadBrowser",
        "sec-ch-ua": '"Chromium";v="104"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "origin": "https://www.kdocs.cn",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://www.kdocs.cn/l/cqykjtCZ18Cj?startTime=1760497134540&from=docs&source=docsWeb&newFile=true&referer=pc_new__0.0.2__wps_win__kdocs__1&mb_id=mwttb6&createEndTime=1760497135732&from2=knewdocs-openBrowserPage&officeType=k&openEnv=hybrid&client_proxy=true&traceId=c4932ec1577c4654b1082ea752b3c01e&sdkversion=3.0.7",
        "accept-language": "zh-CN,zh;q=0.9",
    }

    def __init__(self, cookie_builder: KDocsCookieBuilder):
        self._cookie_builder = cookie_builder

    def _base_headers(self) -> Dict[str, str]:
        headers = dict(self._shared_headers)
        headers["Cookie"] = self._cookie_builder.build()
        return headers

    def for_session(self) -> Dict[str, str]:
        headers = self._base_headers()
        headers.update({
            "accept": "*/*",
            "content-type": "text/plain;charset=UTF-8",
        })
        return headers

    def for_completions(self) -> Dict[str, str]:
        headers = self._base_headers()
        headers.update({
            "accept": "text/event-stream",
            "content-type": "application/json",
        })
        return headers


class KDocsPayloadFactory:
    def session_payload(self, file_id: str) -> str:
        return json.dumps({"file_id": file_id}, ensure_ascii=False)

    def completions_payload(
        self,
        session_id: str,
        question: str,
        active_sheet: Optional[str],
        *,
        include_active_sheet_prefix: bool = True,
    ) -> str:
        body = {
    "session_id": session_id,
            "question": self._build_question(
                question,
                active_sheet,
                include_active_sheet_prefix=include_active_sheet_prefix,
            ),
    "original_question": question,
            "reasoning": False,
        }
        return json.dumps(body, ensure_ascii=False)

    @staticmethod
    def _build_question(
        question: str,
        active_sheet: Optional[str],
        *,
        include_active_sheet_prefix: bool,
    ) -> str:
        if not include_active_sheet_prefix or not active_sheet:
            return question
        return f"现在开始分析当前文件中名为{active_sheet}的工作表，我的问题是：{question}"


class AbstractHttpClient(ABC):
    @abstractmethod
    def post(
        self,
        url: str,
        *,
        headers: Dict[str, str],
        data: str,
        **request_kwargs,
    ) -> requests.Response:
        """Execute HTTP POST request."""


class RequestsHttpClient(AbstractHttpClient):
    def __init__(self, session: Optional[requests.Session] = None, timeout: Optional[float] = 10.0):
        self._session = session or requests.Session()
        self._timeout = timeout

    def post(
        self,
        url: str,
        *,
        headers: Dict[str, str],
        data: str,
        **request_kwargs,
    ) -> requests.Response:
        timeout = request_kwargs.pop("timeout", self._timeout)
        response = self._session.post(
            url,
            headers=headers,
            data=data,
            timeout=timeout,
            **request_kwargs,
        )
        return response


class KDocsAnalysisService:
    def __init__(
        self,
        *,
        credentials: Optional[KDocsCredentials] = None,
        headers_builder: Optional[KDocsHeadersBuilder] = None,
        http_client: Optional[AbstractHttpClient] = None,
        payload_factory: Optional[KDocsPayloadFactory] = None,
        endpoints: Optional[KDocsEndpoints] = None,
    ) -> None:
        creds = credentials or KDocsCredentials.from_env()
        cookie_builder = KDocsCookieBuilder(creds)
        self._headers_builder = headers_builder or KDocsHeadersBuilder(cookie_builder)
        self._http_client = http_client or RequestsHttpClient()
        self._payload_factory = payload_factory or KDocsPayloadFactory()
        self._endpoints = endpoints or KDocsEndpoints()

    def create_session(self, file_id: str) -> dict:
        payload = self._payload_factory.session_payload(file_id)
        response = self._http_client.post(
            f"{self._endpoints.sessions}?plt_2_echarts=true",
            headers=self._headers_builder.for_session(),
            data=payload,
            verify=False,
        )
        self._raise_for_status(response)
        return response.json()

    def request_completions(
        self,
        session_id: str,
        question: str,
        active_sheet: Optional[str],
        *,
        include_active_sheet_prefix: bool = False,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> str:
        payload = self._payload_factory.completions_payload(
            session_id,
            question,
            active_sheet,
            include_active_sheet_prefix=include_active_sheet_prefix,
        )
        headers = self._headers_builder.for_completions()
        if extra_headers:
            headers.update(extra_headers)
        response = self._http_client.post(
            self._endpoints.completions(session_id),
            headers=headers,
            data=payload,
            verify=False,
        )
        self._raise_for_status(response)
        return response.text

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise RuntimeError(f"KDocs 接口请求失败: {error}") from error


_default_service: Optional[KDocsAnalysisService] = None


def _get_service() -> KDocsAnalysisService:
    global _default_service
    if _default_service is None:
        _default_service = KDocsAnalysisService()
    return _default_service


def get_session_id(file_id: str) -> dict:
    return _get_service().create_session(file_id)


def get_completions(
    session_id: str,
    question: str,
    active_sheet: Optional[str],
    *,
    include_active_sheet_prefix: bool = False,
    extra_headers: Optional[Dict[str, str]] = None,
) -> str:
    return _get_service().request_completions(
        session_id,
        question,
        active_sheet,
        include_active_sheet_prefix=include_active_sheet_prefix,
        extra_headers=extra_headers,
    )


__all__ = [
    "KDocsAnalysisService",
    "KDocsCredentials",
    "KDocsEndpoints",
    "KDocsHeadersBuilder",
    "KDocsPayloadFactory",
    "RequestsHttpClient",
    "get_session_id",
    "get_completions",
]
