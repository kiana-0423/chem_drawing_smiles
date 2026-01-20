# 化学结构绘制与 SMILES 转换工具

本项目以网页形式提供化学结构绘制与 SMILES 转换功能，前端基于 Kekule.js 生成和解析 SMILES：

- **浏览器版 (`web_app.py`)**：内置简易 HTTP 服务，直接在浏览器中打开独立的 HTML 页面，快速查看和生成 SMILES。
- **桌面版 (`app.py`)**：使用 PySide6 + QtWebEngine 将编辑器嵌入到原生窗口中，适合需要本地桌面体验的场景。

> 注意：两种形态都通过 CDN 加载 Kekule 资源，运行环境需具备外网访问能力。若计划离线使用，需要将相应静态文件缓存到本地并更新 HTML 中的引用路径。

## 功能特性
- 交互式化学结构绘制（原子、键、环、链等工具）
- 结构变更时实时刷新 SMILES 文本
- 支持从 SMILES 重建结构
- 一键复制 SMILES / 清空画布
- 桌面版附带状态栏提示与剪贴板集成

## 目录结构
```
├── app.py                     # PySide6 桌面程序入口
├── web_app.py                 # 简易静态服务与浏览器入口
├── resources/
│   └── editor.html            # 桌面版加载的 HTML 模板
└── templates/
    └── standalone_editor.html # 浏览器版 HTML 模板
```

## 环境要求
- Python 3.9+
- 桌面版依赖：`PySide6`, `PySide6-QtWebEngine`
- 浏览器版仅使用标准库

建议创建虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate        # Windows 使用 .venv\Scripts\activate
pip install PySide6 PySide6-QtWebEngine
```

## 运行浏览器版
```bash
python web_app.py
# 默认监听 http://127.0.0.1:5173/ 并自动尝试打开浏览器
```

可选参数：
```bash
python web_app.py --port 8080      # 指定端口
python web_app.py --no-browser     # 仅启动服务，不自动打开浏览器
```

浏览器中将呈现与桌面版一致的功能，支持 SMILES 显示、复制、导入与画布清空。

## 运行桌面版
```bash
python app.py
```

启动后将打开一个 Qt 窗口：
- 左侧为 Kekule 画布，可直接绘制结构；
- 右侧面板展示实时 SMILES，支持复制；
- 输入框可粘贴 SMILES 并点击“载入结构”恢复画布；
- “清空画布”按钮用于快速重置。

## 离线使用提示
若网络受限，可将 Kekule 相关资源下载到本地，并修改下列文件中的 `<script>` / `<link>` 地址：

- `resources/editor.html`
- `templates/standalone_editor.html`

例如，将文件放入 `resources/kekule/`，然后将引用改为相对路径 `./kekule/...`。

## 常见问题
- **启动浏览器失败**：`web_app.py` 会打印访问地址，手动复制到浏览器即可。
- **SMILES 文本为空**：确保当前画布包含结构；清空画布后输出会变为空字符串。
- **无法访问 CDN**：请参考“离线使用提示”章节，改用本地资源。

## 后续扩展建议
- 将 Kekule 资源本地化，提供完全离线的体验。
- 增加导入 / 导出 Molfile 等格式的 UI。
- 集成 RDKit 或 Open Babel，对 SMILES 进行规范化、性质计算或子结构搜索。
