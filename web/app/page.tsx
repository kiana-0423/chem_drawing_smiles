import dynamic from "next/dynamic";
import styles from "./page.module.css";

const KetcherEditor = dynamic(() => import("../components/KetcherEditor"), {
  ssr: false,
});

export default function Page() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>在线化学结构编辑器</h1>
        <p className={styles.subtitle}>
          使用 Ketcher 绘制结构并导出 SMILES/MOL，支持图片 OCR 导入。
        </p>
      </header>
      <section className={styles.editorCard}>
        <KetcherEditor />
      </section>
    </main>
  );
}
