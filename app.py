from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView


BASE_DIR = Path(__file__).resolve().parent
EDITOR_HTML = BASE_DIR / "resources" / "editor.html"


class Bridge(QObject):
    """Bridge object exposed to the embedded web editor."""

    page_ready = Signal()
    smiles_changed = Signal(str)

    @Slot()
    def pageReady(self) -> None:
        """Called by the page when initial resources are ready."""
        self.page_ready.emit()

    @Slot(str)
    def updateSmiles(self, smiles: str) -> None:
        """Receive SMILES updates emitted by the web editor."""
        self.smiles_changed.emit(smiles or "")


class MainWindow(QMainWindow):
    """Main GUI window embedding the chemical editor and auxiliary controls."""

    def __init__(self) -> None:
        super().__init__()
        if not EDITOR_HTML.exists():
            raise FileNotFoundError(f"Missing editor template: {EDITOR_HTML}")

        self.setWindowTitle("化学结构编辑器（Qt）")
        self.resize(1200, 720)

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        self.setCentralWidget(central)

        self.web_view = QWebEngineView(self)
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.web_view, stretch=3)

        side_panel = QWidget(self)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(10)

        side_layout.addWidget(QLabel("<b>当前 SMILES</b>", side_panel))

        self.smiles_display = QPlainTextEdit(side_panel)
        self.smiles_display.setReadOnly(True)
        self.smiles_display.setPlaceholderText("SMILES 将显示在此处。")
        self.smiles_display.setMaximumBlockCount(1)
        side_layout.addWidget(self.smiles_display)

        copy_button = QPushButton("复制 SMILES", side_panel)
        copy_button.clicked.connect(self.copy_smiles)
        side_layout.addWidget(copy_button)

        side_layout.addWidget(QLabel("<b>导入 SMILES</b>", side_panel))

        self.smiles_input = QLineEdit(side_panel)
        self.smiles_input.setPlaceholderText("在此输入 SMILES 后点击载入")
        side_layout.addWidget(self.smiles_input)

        load_button = QPushButton("载入结构", side_panel)
        load_button.clicked.connect(self.load_smiles_from_input)
        side_layout.addWidget(load_button)

        clear_button = QPushButton("清空画布", side_panel)
        clear_button.clicked.connect(self.clear_structure)
        side_layout.addWidget(clear_button)

        side_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        tips = QLabel(
            "提示：\n"
            "· 左侧画布提供原子、键、环等绘制工具；\n"
            "· 每次编辑会实时同步 SMILES；\n"
            "· 载入 SMILES 可快速重建结构。",
            side_panel,
        )
        tips.setWordWrap(True)
        side_layout.addWidget(tips)

        layout.addWidget(side_panel, stretch=2)

        self.status = self.statusBar()
        self.status.showMessage("正在加载编辑器资源…")

        self.channel = QWebChannel(self)
        self.bridge = Bridge(self)
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        self.bridge.page_ready.connect(self.on_page_ready)
        self.bridge.smiles_changed.connect(self.on_smiles_changed)

        self.current_smiles: str = ""
        self._load_editor()

    # -- setup helpers -------------------------------------------------------------

    def _load_editor(self) -> None:
        url = EDITOR_HTML.as_uri()
        self.web_view.setUrl(url)

    def run_js(self, script: str) -> None:
        self.web_view.page().runJavaScript(script)

    # -- bridge callbacks ----------------------------------------------------------

    def on_page_ready(self) -> None:
        self.status.showMessage("编辑器已就绪。")
        self.run_js("refreshSmiles && refreshSmiles();")

    def on_smiles_changed(self, smiles: str) -> None:
        self.current_smiles = smiles
        if smiles:
            self.smiles_display.setPlainText(smiles)
            self.status.showMessage("SMILES 已更新。")
        else:
            self.smiles_display.setPlainText("")
            self.status.showMessage("当前画布为空。")

    # -- UI handlers ---------------------------------------------------------------

    def copy_smiles(self) -> None:
        if not self.current_smiles:
            QMessageBox.information(self, "提示", "当前没有可复制的 SMILES。")
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.current_smiles, mode=clipboard.Clipboard)
        self.status.showMessage("SMILES 已复制到剪贴板。")

    def load_smiles_from_input(self) -> None:
        smiles = self.smiles_input.text().strip()
        if not smiles:
            QMessageBox.information(self, "提示", "请输入有效的 SMILES。")
            return
        escaped = json.dumps(smiles)
        self.run_js(f"loadSmiles && loadSmiles({escaped});")
        self.status.showMessage("正在载入 SMILES…")

    def clear_structure(self) -> None:
        self.run_js("clearStructure && clearStructure();")
        self.status.showMessage("画布已清空。")


def main() -> None:
    # Enable shared OpenGL contexts for WebEngine stability in some environments.
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
