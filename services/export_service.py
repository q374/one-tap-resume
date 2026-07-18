import io


class ExportService:
    def to_pdf(self, html_content: str) -> bytes:
        """将HTML简历导出。优先尝试服务端PDF，失败时返回HTML供浏览器打印"""
        # 尝试 xhtml2pdf（可能中文支持不佳）
        try:
            from xhtml2pdf import pisa
            import tempfile, os

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                with open(tmp_path, 'wb') as f:
                    pisa.CreatePDF(html_content, dest=f, encoding='utf-8')
                with open(tmp_path, 'rb') as f:
                    pdf_bytes = f.read()
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            if len(pdf_bytes) > 500:
                return pdf_bytes
        except Exception:
            pass

        # 降级：返回 HTML，前端用浏览器打印为PDF
        raise RuntimeError(
            "服务端PDF生成暂不可用（xhtml2pdf对中文支持有限）。"
            "请使用浏览器的 Ctrl+P → 另存为PDF 功能导出。"
            "预览效果即为最终效果。"
        )


export_service = ExportService()
