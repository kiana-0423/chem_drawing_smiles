"use client";

import { useCallback, useRef, useState } from "react";
import { Ketcher } from "ketcher-react";
import { StandaloneStructServiceProvider } from "ketcher-standalone";
import styles from "./KetcherEditor.module.css";

type KetcherInstance = {
  getSmiles: () => Promise<string>;
  getMolfile: () => Promise<string>;
  setMolecule: (mol: string) => Promise<void>;
};

type StatusKind = "idle" | "info" | "success" | "error";

type StatusState = {
  kind: StatusKind;
  message: string;
};

const structServiceProvider = new StandaloneStructServiceProvider();

export default function KetcherEditor() {
  const [ketcher, setKetcher] = useState<KetcherInstance | null>(null);
  const [status, setStatus] = useState<StatusState>({
    kind: "idle",
    message: "准备就绪。",
  });
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const setStatusMessage = useCallback((kind: StatusKind, message: string) => {
    setStatus({ kind, message });
  }, []);

  const handleCopySmiles = useCallback(async () => {
    if (!ketcher) {
      setStatusMessage("error", "编辑器尚未加载完成。");
      return;
    }
    try {
      const smiles = await ketcher.getSmiles();
      if (!smiles) {
        setStatusMessage("error", "当前结构为空，无法复制。");
        return;
      }
      await navigator.clipboard.writeText(smiles);
      setStatusMessage("success", "SMILES 已复制到剪贴板。");
    } catch (error) {
      setStatusMessage("error", "复制失败，请稍后重试。");
    }
  }, [ketcher, setStatusMessage]);

  const handleDownloadMol = useCallback(async () => {
    if (!ketcher) {
      setStatusMessage("error", "编辑器尚未加载完成。");
      return;
    }
    try {
      const molfile = await ketcher.getMolfile();
      if (!molfile) {
        setStatusMessage("error", "当前结构为空，无法下载。");
        return;
      }
      const blob = new Blob([molfile], { type: "chemical/x-mdl-molfile" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "structure.mol";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setStatusMessage("success", "MOL 文件已下载。");
    } catch (error) {
      setStatusMessage("error", "下载失败，请稍后重试。");
    }
  }, [ketcher, setStatusMessage]);

  const handleImportExample = useCallback(async () => {
    if (!ketcher) {
      setStatusMessage("error", "编辑器尚未加载完成。");
      return;
    }
    try {
      await ketcher.setMolecule("c1ccccc1");
      setStatusMessage("success", "示例苯环已导入。");
    } catch (error) {
      setStatusMessage("error", "导入失败，请稍后重试。");
    }
  }, [ketcher, setStatusMessage]);

  const handleOcrPick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleOcrUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }
      event.target.value = "";

      if (!ketcher) {
        setStatusMessage("error", "编辑器尚未加载完成。");
        return;
      }

      const ocrUrl = process.env.NEXT_PUBLIC_OCR_URL;
      if (!ocrUrl) {
        setStatusMessage("error", "未配置 OCR 服务地址。");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);

      setStatusMessage("info", "图片已上传，正在识别...。");

      try {
        const response = await fetch(ocrUrl, {
          method: "POST",
          body: formData,
        });
        const result = (await response.json()) as {
          ok: boolean;
          smiles?: string;
          error?: string;
        };

        if (!response.ok || !result.ok || !result.smiles) {
          setStatusMessage(
            "error",
            result.error || "OCR 识别失败，请更换图片。"
          );
          return;
        }

        await ketcher.setMolecule(result.smiles);
        setStatusMessage("success", "OCR 导入成功。");
      } catch (error) {
        setStatusMessage("error", "OCR 服务请求失败，请稍后重试。");
      }
    },
    [ketcher, setStatusMessage]
  );

  return (
    <div className={styles.wrapper}>
      <div className={styles.toolbar}>
        <button
          className={styles.button}
          type="button"
          onClick={handleCopySmiles}
        >
          复制 SMILES
        </button>
        <button
          className={styles.button}
          type="button"
          onClick={handleDownloadMol}
        >
          下载 MOL
        </button>
        <button
          className={styles.button}
          type="button"
          onClick={handleImportExample}
        >
          导入示例苯
        </button>
        <button
          className={styles.buttonAccent}
          type="button"
          onClick={handleOcrPick}
        >
          图片 OCR 导入
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className={styles.fileInput}
          onChange={handleOcrUpload}
        />
        <span className={`${styles.status} ${styles[status.kind]}`}>
          {status.message}
        </span>
      </div>
      <div className={styles.editor}>
        <Ketcher
          structServiceProvider={structServiceProvider}
          onInit={(instance) => setKetcher(instance as KetcherInstance)}
        />
      </div>
    </div>
  );
}
