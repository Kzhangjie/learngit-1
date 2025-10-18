import os
import urllib.parse

import requests


def download_image(url, save_path=None):
    """
    下载图片
    """
    try:
        # 发送GET请求下载图片
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # 如果没有指定保存路径，从URL参数中提取文件名
        if save_path is None:
            # 解析URL参数
            parsed_url = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed_url.query)

            # 从response-content-disposition参数中提取文件名
            if "response-content-disposition" in params:
                disposition = params["response-content-disposition"][0]
                # 解析文件名
                if "filename=" in disposition:
                    filename = disposition.split("filename=")[1]
                    filename = urllib.parse.unquote(filename)
                    save_path = filename
                else:
                    save_path = "downloaded_image.png"
            else:
                save_path = "downloaded_image.png"

        # 保存图片
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"图片已成功下载到: {save_path}")
        return save_path

    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        return None


if __name__ == "__main__":
    # 图片URL
    image_url = "https://weboffice-kdocs-openapi-test.ks3-cn-beijing.ksyun.com/lingxi/ai_images/watermark/2025/6/23_677b17731763cedbf68eca65bc880e62e01ae5b0.jpeg_thumb_max_edge_400?Expires=1751273382&KSSAccessKeyId=AKLTkZscKjFpQX2F7xRLSi20&Signature=etSWfpf4IfETMivFg%2FmyeejTwPQ%3D&response-content-disposition=attachment%3B+filename%3D%E7%8C%AB%281%29.png"

    # 下载图片
    download_image(image_url)
