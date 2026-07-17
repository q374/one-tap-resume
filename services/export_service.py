import io

class ExportService:
    def to_pdf(self, html_content: str) -> bytes:
        """将 HTML 转为 PDF，返回字节流"""
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except ImportError:
            raise RuntimeError("WeasyPrint 未安装。请运行: pip install weasyprint")
        except Exception as e:
            raise RuntimeError(f"PDF 生成失败: {str(e)}")


export_service = ExportService()
