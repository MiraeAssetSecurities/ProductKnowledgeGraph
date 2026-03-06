import json
import logging
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.pipeline_options_vlm_model import (
    ApiVlmOptions,
    ResponseFormat,
)
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

from pydantic.json import pydantic_encoder

# --------------------------------------------------
# OpenAI-compatible VLM options (PROXY 기반)
# --------------------------------------------------
def openai_compatible_vlm_options(
    model: str,
    prompt: str,
    format: ResponseFormat,
    hostname_and_port: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    api_key: str = "",
    skip_special_tokens: bool = False,
):
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    return ApiVlmOptions(
        url=f"http://{hostname_and_port}/v1/chat/completions",
        params=dict(
            model=model,
            max_tokens=max_tokens,
            #skip_special_tokens=skip_special_tokens,
        ),
        headers=headers,
        prompt=prompt,
        timeout=90,
        scale=2.0,
        temperature=temperature,
        response_format=format,
    )


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    logging.basicConfig(level=logging.INFO)

    # 처리할 문서들 (여러 포맷)
    input_paths = [
        #Path("(ISA공통)ISA 이수관 전문미사용기관 처리 안내.pdf"),
        Path("[8951] 표준메시지_반대의사_20210305.xlsx"),
        #Path("abc.png"),
        #Path("abc.docx"),
        #Path("abc.pptx"),
        #Path("abc.md"),
        #Path("abc.csv"),
    ]

    # ----------------------------------------------
    # VLM Pipeline 옵션
    # ----------------------------------------------
    pipeline_options = VlmPipelineOptions(
        enable_remote_services=True
    )

    pipeline_options.vlm_options = openai_compatible_vlm_options(
        model="bedrock-qwen3-v1",
        hostname_and_port="54.197.26.233:4000",
        prompt="OCR the full page to markdown.",
        format=ResponseFormat.MARKDOWN,
        api_key="KEY_AAA",
    )

    # ----------------------------------------------
    # DocumentConverter (멀티 포맷 + VLM)
    # ----------------------------------------------
    doc_converter = DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.IMAGE,
            InputFormat.DOCX,
            InputFormat.PPTX,
            InputFormat.XLSX,
            InputFormat.HTML,
            InputFormat.CSV,
            InputFormat.MD,
        ],
        format_options={
            # PDF → VLM Pipeline
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
                #backend=PyPdfiumDocumentBackend,
            ),
            # IMAGE → VLM Pipeline
            InputFormat.IMAGE: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
            ),
            # DOCX → 일반 파이프라인 (텍스트 중심)
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline
            ),
            InputFormat.XLSX: WordFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend,
            ),
            InputFormat.CSV: WordFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
            ),
            InputFormat.HTML: WordFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
            ),
        },
    )

    results = doc_converter.convert_all(input_paths)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    from pydantic import AnyUrl
    from collections.abc import Mapping, Sequence

    def make_json_safe(obj):
        if isinstance(obj, AnyUrl):
            return str(obj)
        elif isinstance(obj, Mapping):
            return {k: make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
            return [make_json_safe(v) for v in obj]
        else:
            return obj

    for res in results:
        doc = res.document
        stem = res.input.file.stem


        # Markdown
        with open(out_dir / f"{stem}.md", "w") as f:
            f.write(doc.export_to_markdown())

        # Lossless JSON
        lossless = doc.export_to_dict(mode="lossless")
        safe_lossless = make_json_safe(lossless)

        with open(out_dir / f"{stem}.lossless.json", "w", encoding="utf-8") as f:
            json.dump(
                safe_lossless,
                f,
                ensure_ascii=False,
                indent=2,
            )
        logging.info(f"✔ Converted with VLM: {res.input.file.name}")


if __name__ == "__main__":
    main()
