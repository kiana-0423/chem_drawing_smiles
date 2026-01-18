import os
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

cors_origins = os.getenv("CORS_ORIGINS", "*")
allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    if not file.filename:
        return {"ok": False, "error": "未上传文件。"}

    suffix = Path(file.filename).suffix or ".png"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / f"input{suffix}"
        output_path = Path(tmpdir) / "out.smi"

        content = await file.read()
        if not content:
            return {"ok": False, "error": "文件内容为空。"}

        input_path.write_bytes(content)

        cmd = ["osra", "--write", str(output_path), str(input_path)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "osra 执行失败").strip()
            return {"ok": False, "error": detail}

        if not output_path.exists():
            return {"ok": False, "error": "未生成 SMILES 输出。"}

        line = output_path.read_text(encoding="utf-8").strip()
        if not line:
            return {"ok": False, "error": "SMILES 结果为空。"}

        smiles = line.split()[0]
        return {"ok": True, "smiles": smiles}
