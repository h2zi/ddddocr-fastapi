import base64
import io

import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_ocr_image() -> bytes:
    """生成一张带文字的简单验证码图片"""
    img = Image.new("RGB", (160, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 15), "A1B2", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_solid_image(width=200, height=100, color=(128, 128, 128)) -> bytes:
    """生成一张纯色图片"""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


OCR_IMG = make_ocr_image()
OCR_IMG_B64 = base64.b64encode(OCR_IMG).decode()
SOLID_IMG = make_solid_image()
SOLID_IMG_B64 = base64.b64encode(SOLID_IMG).decode()


# ========== OCR 接口 ==========

class TestOCR:
    def test_file_upload(self):
        resp = client.post("/ocr", files={"file": ("captcha.png", OCR_IMG, "image/png")})
        data = resp.json()
        assert resp.status_code == 200
        assert data["code"] == 200
        assert isinstance(data["data"], str)

    def test_base64(self):
        resp = client.post("/ocr", data={"image": OCR_IMG_B64})
        data = resp.json()
        assert data["code"] == 200
        assert isinstance(data["data"], str)

    def test_base64_data_uri(self):
        resp = client.post("/ocr", data={"image": f"data:image/png;base64,{OCR_IMG_B64}"})
        assert resp.json()["code"] == 200

    def test_probability_returns_dict(self):
        resp = client.post(
            "/ocr",
            files={"file": ("captcha.png", OCR_IMG, "image/png")},
            data={"probability": "true"},
        )
        data = resp.json()
        assert data["code"] == 200
        # probability 模式返回 dict
        assert isinstance(data["data"], (dict, list))

    def test_no_input_returns_400(self):
        resp = client.post("/ocr")
        assert resp.json()["code"] == 400

    def test_invalid_base64(self):
        resp = client.post("/ocr", data={"image": "!!!not-base64!!!"})
        assert resp.status_code == 400


# ========== 滑块匹配接口 ==========

class TestSlideMatch:
    def test_file_upload(self):
        target = make_solid_image(50, 50, (255, 0, 0))
        background = make_solid_image(300, 200, (0, 0, 255))
        resp = client.post(
            "/slide_match",
            files={
                "target_file": ("target.png", target, "image/png"),
                "background_file": ("bg.png", background, "image/png"),
            },
        )
        data = resp.json()
        assert resp.status_code == 200
        assert data["code"] == 200
        assert isinstance(data["data"], dict)

    def test_base64(self):
        target_b64 = base64.b64encode(make_solid_image(50, 50)).decode()
        bg_b64 = base64.b64encode(make_solid_image(300, 200)).decode()
        resp = client.post("/slide_match", data={"target": target_b64, "background": bg_b64})
        data = resp.json()
        assert data["code"] == 200


# ========== 目标检测接口 ==========

class TestDetection:
    def test_file_upload(self):
        resp = client.post("/detection", files={"file": ("test.png", OCR_IMG, "image/png")})
        data = resp.json()
        assert resp.status_code == 200
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_base64(self):
        resp = client.post("/detection", data={"image": OCR_IMG_B64})
        data = resp.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)

    def test_no_input_returns_400(self):
        resp = client.post("/detection")
        assert resp.json()["code"] == 400


# ========== decode_image 单元测试 ==========

class TestDecodeImage:
    @pytest.mark.anyio
    async def test_decode_base64(self):
        from app.main import decode_image
        result = await decode_image(OCR_IMG_B64)
        assert result == OCR_IMG

    @pytest.mark.anyio
    async def test_decode_data_uri(self):
        from app.main import decode_image
        result = await decode_image(f"data:image/png;base64,{OCR_IMG_B64}")
        assert result == OCR_IMG

    @pytest.mark.anyio
    async def test_none_raises_400(self):
        from fastapi import HTTPException
        from app.main import decode_image
        with pytest.raises(HTTPException) as exc_info:
            await decode_image(None)
        assert exc_info.value.status_code == 400
