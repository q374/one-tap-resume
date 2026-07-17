import os
import tempfile

class OCRService:
    async def extract_text(self, image_paths: list[str]) -> str:
        all_text = []
        for path in image_paths:
            text = await self._ocr_single(path)
            if text:
                all_text.append(text)
        return "\n\n--- 下一页 ---\n\n".join(all_text)

    async def _ocr_single(self, image_path: str) -> str:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            return text.strip()
        except ImportError:
            return f"[Tesseract OCR 未安装，无法识别图片: {os.path.basename(image_path)}]"
        except Exception as e:
            return f"[OCR 识别失败: {str(e)}]"


ocr_service = OCRService()
