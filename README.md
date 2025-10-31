# 化学结构绘制与 SMILES 转换程序设计方案

## 目标与核心功能
- 提供一个网页应用，支持用户交互式地绘制有机及无机化学结构。
- 将当前绘制的结构实时导出为 SMILES，并支持复制、下载、批量导出。
- 兼容常见结构文件（Molfile、SDF、SMILES）的导入 / 导出，并提供基础验证与提示。

## 推荐技术栈
- **前端框架**：React + Vite（轻量、热更新快、TS 友好）。
- **化学编辑器**：`@epam/ketcher` 开源库（界面体验接近 ChemDraw / Ketcher Web）。
  - 提供绘制画布、模板库、原子/键编辑、环结构、手性配置等交互。
  - 内置使用 `ketcher-core` + `molfile-converter`，可获取 SMILES/Molfile。
- **辅助化学库（可选）**：`openchemlib-js` 用于额外的格式转换、性质计算。
- **后端（可选）**：FastAPI + RDKit，用于生成规范化 SMILES、InChIKey、子结构搜索等增强能力。
  - 如果部署在纯前端环境，可暂时省略，直接利用 Ketcher 的本地转换函数。

## 系统架构
```
┌───────────────────┐
│      React UI     │
│ ┌───────────────┐ │
│ │ Ketcher Canvas│ │ ⇄ 用户绘制操作
│ └───────────────┘ │
│       ↓             │ 获取结构数据 (Molfile/SMILES)
│  State / Hooks      │
└────────┬───────────┘
         │ fetch API（可选）
         ▼
┌───────────────────┐
│   FastAPI 服务     │
│  · /convert/smiles │ ← RDKit 调用
│  · /analyse        │
└───────────────────┘
```

### 前端功能划分
1. **EditorContainer**：封装 Ketcher 组件，负责初始化、事件绑定（`onChange`, `onStructChange`）。
2. **ToolbarPanel**：在默认工具栏基础上增加常用操作（重置、撤销、模板快速插入）。
3. **SmilesPanel**：
   - 实时显示 SMILES。
   - 提供复制、下载 `.smi` 按钮。
   - 可切换“Canonical / Isomeric / Kekulé”视图（调用后端或 `openchemlib` 处理）。
4. **ImportExportModal**：处理 Molfile/SMILES 粘贴导入，或文件上传下载。
5. **ValidationToast**：简单的结构校验提示（空结构、未闭合环、价键警告等）。

### 后端接口（可选增强）
| HTTP | 路径 | 功能 | 请求示例 |
| ---- | ---- | ---- | -------- |
| POST | `/convert/smiles` | 将前端导出的 Molfile 转换为规范 SMILES | `{ "molfile": "..." }` |
| POST | `/analyse/properties` | 返回分子量、logP、HBA/HBD 等性质 | `{ "smiles": "..." }` |
| POST | `/search/substructure` | 子结构搜索 | `{ "query": "c1ccccc1", "targets": ["..."] }` |

FastAPI 伪代码：
```python
from fastapi import FastAPI
from pydantic import BaseModel
from rdkit import Chem

app = FastAPI()

class MolfilePayload(BaseModel):
    molfile: str

@app.post("/convert/smiles")
def convert_smiles(payload: MolfilePayload):
    mol = Chem.MolFromMolBlock(payload.molfile, sanitize=True)
    if mol is None:
        return {"success": False, "error": "Invalid molfile"}
    smiles = Chem.MolToSmiles(mol, canonical=True)
    return {"success": True, "smiles": smiles}
```

## 关键实现步骤
1. **初始化项目**
   ```bash
   npm create vite@latest chem-editor -- --template react-ts
   cd chem-editor
   npm install
   npm install @epam/ketcher @epam/panel @types/node openchemlib
   ```
2. **封装 Ketcher 组件**
   ```tsx
   // src/components/ChemEditor.tsx
   import { useEffect, useRef } from "react";
   import { Ketcher } from "ketcher-react";
   import "ketcher-react/dist/index.css";

   export function ChemEditor({ onSmilesChange }: { onSmilesChange: (s: string) => void }) {
     const ketcherRef = useRef<any>(null);

     useEffect(() => {
       const ketcher = ketcherRef.current?.getKetcher?.();
       if (!ketcher) return;
       const handler = async () => {
         const struct = await ketcher.getSmiles();
         onSmilesChange(struct);
       };
       ketcher.subscribe("change", handler);
       return () => ketcher.unsubscribe("change", handler);
     }, []);

     return <Ketcher ref={ketcherRef} staticResourcesUrl="/ketcher" />;
   }
   ```
   - 将 `ketcher-core` 所需的静态文件放到 `public/ketcher`。
   - 添加 Suspense/loading 保证资源加载顺畅。
3. **构建 SMILES 面板**
   ```tsx
   // src/components/SmilesPanel.tsx
   export function SmilesPanel({ smiles }: { smiles: string }) {
     return (
       <section>
         <header>SMILES</header>
         <code>{smiles || "（当前为空）"}</code>
         <button onClick={() => navigator.clipboard.writeText(smiles)}>复制</button>
       </section>
     );
   }
   ```
4. **页面组合**
   ```tsx
   // src/App.tsx
   import { useState } from "react";
   import { ChemEditor } from "./components/ChemEditor";
   import { SmilesPanel } from "./components/SmilesPanel";

   export default function App() {
     const [smiles, setSmiles] = useState("");
     return (
       <main className="layout">
         <ChemEditor onSmilesChange={setSmiles} />
         <SmilesPanel smiles={smiles} />
       </main>
     );
   }
   ```

## UX 细节与扩展
- 模仿参考站点，提供左右布局：左侧画布 + 右侧属性面板。
- 记住用户最近结构（LocalStorage）。
- 导入/导出历史记录，快速恢复。
- 可选：增加 3D 查看（调用 `3Dmol.js`）和 AI 生成初始骨架。

## 部署建议
- 单纯的前端：部署至静态托管（Vercel、Netlify、OSS）。
- 需要 RDKit：使用 Docker 镜像（`continuumio/miniconda3` + `conda install -c rdkit rdkit`），将 FastAPI 部署到云服务器或 Kubernetes，前端通过环境变量配置 API URL。
- 若需离线桌面版，可利用 Tauri / Electron 打包。

## 下一步工作
1. 明确是否需要后端增强（规范化、搜索、属性计算），决定是否集成 RDKit。
2. 下载并放置 `ketcher-core` 静态资源（参考官方发布包），避免线上依赖。
3. 实现初版 UI 与 SMILES 实时显示，验证主路径。
4. 完成导入/导出、错误提示、国际化等增强功能。

完成以上步骤后即可实现与参考站点功能相近的化学结构绘制与 SMILES 转换应用。

---

## Python 桌面原型（PySide6）
仓库中提供了一个基于 PySide6（Qt）与 Kekule.js 的桌面化学编辑器原型，直接在 GUI 中绘制结构并同步 SMILES。

### 运行本地示例
```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install PySide6 PySide6-QtWebEngine
python app.py
```

程序启动后会在桌面显示编辑器窗口：中央为 Kekule.js 画布，侧边面板可查看 SMILES、复制到剪贴板，或输入新的 SMILES 并载入到画布中。Kekule.js 资源通过 CDN 加载，运行环境需具备网络访问能力；若需离线使用，请将相关静态文件下载至 `resources/` 并在 `resources/editor.html` 中修改引用路径。
