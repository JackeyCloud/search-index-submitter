from __future__ import annotations

import sys
from dataclasses import fields

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import AppConfig
from .engine import run_submissions
from .models import SubmissionResult
from .targets import parse_targets


APP_STYLE = """
QWidget { background: #0b1220; color: #dbe7ff; font-size: 14px; }
QMainWindow { background: #07101f; }
QFrame#Card { background: #111c2f; border: 1px solid #20304b; border-radius: 14px; }
QLabel#Title { font-size: 28px; font-weight: 700; color: #f6f9ff; }
QLabel#Subtitle { color: #89a0c2; font-size: 13px; }
QLabel#Section { font-size: 16px; font-weight: 650; color: #eef4ff; }
QTextEdit, QLineEdit, QSpinBox { background: #091426; border: 1px solid #2a3c5a; border-radius: 8px; padding: 9px; selection-background-color: #2475e8; }
QTextEdit:focus, QLineEdit:focus { border: 1px solid #4b96ff; }
QPushButton { background: #1b2b43; border: 1px solid #304765; border-radius: 8px; padding: 9px 16px; font-weight: 600; }
QPushButton:hover { background: #243a5a; }
QPushButton#Primary { background: #2475e8; border-color: #3f8cff; color: white; }
QPushButton#Primary:hover { background: #3182f3; }
QPushButton#Preview { background: #173f3b; border-color: #24685f; color: #95f2df; }
QPushButton:disabled { color: #65748a; background: #142033; }
QCheckBox { spacing: 7px; color: #c8d8f0; }
QTableWidget { background: #0b1628; alternate-background-color: #101d31; border: 1px solid #20304b; border-radius: 9px; gridline-color: #1d2b42; }
QHeaderView::section { background: #16243a; color: #9eb4d3; padding: 8px; border: 0; border-right: 1px solid #263750; font-weight: 600; }
QToolTip { background: #192942; color: white; border: 1px solid #3b5375; }
"""


PROVIDERS = [
    ("indexnow", "IndexNow", "一次通知 Bing、Yandex 等参与平台"),
    ("baidu", "百度", "百度搜索资源平台普通收录 API"),
    ("google", "Google", "Search Console Sitemap API"),
    ("bing", "Bing API", "Bing Webmaster URL Submission API"),
    ("yandex", "Yandex Sitemap", "Yandex Webmaster Sitemap API"),
    ("360", "360 搜索", "无稳定公开 API，显示人工入口"),
    ("shenma", "神马搜索", "无稳定公开 API，显示人工入口"),
]


class SubmissionWorker(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, text: str, sitemap: str, providers: list[str], config: AppConfig, dry_run: bool, check_existing: bool):
        super().__init__()
        self.text = text
        self.sitemap = sitemap
        self.providers = providers
        self.config = config
        self.dry_run = dry_run
        self.check_existing = check_existing

    def run(self) -> None:
        try:
            targets = parse_targets(self.text, self.sitemap)
            run_submissions(
                targets,
                self.providers,
                self.config,
                dry_run=self.dry_run,
                check_existing=self.check_existing,
                callback=self.result.emit,
            )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class ConfigDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("平台凭据配置")
        self.setMinimumWidth(620)
        self.config = config
        layout = QVBoxLayout(self)
        hint = QLabel("凭据仅保存在 ~/.search-index-submitter/config.json，并设置为仅当前用户可读。")
        hint.setObjectName("Subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        form.setSpacing(12)
        self.inputs: dict[str, QLineEdit | QSpinBox] = {}
        labels = {
            "indexnow_key": "IndexNow Key",
            "indexnow_key_location": "Key 文件 URL（可选）",
            "baidu_token": "百度 token",
            "baidu_token_map": "百度多站 token（域名=token，逗号分隔）",
            "bing_api_key": "Bing API Key",
            "google_client_secrets": "Google OAuth 客户端 JSON",
            "google_token_file": "Google Token 缓存（可选）",
            "yandex_oauth_token": "Yandex OAuth Token",
            "request_timeout": "请求超时（秒）",
        }
        secret_fields = {"indexnow_key", "baidu_token", "bing_api_key", "yandex_oauth_token"}
        for field in fields(AppConfig):
            value = getattr(config, field.name)
            if field.name == "request_timeout":
                widget = QSpinBox()
                widget.setRange(5, 120)
                widget.setValue(int(value))
            else:
                widget = QLineEdit(str(value))
                if field.name in secret_fields:
                    widget.setEchoMode(QLineEdit.EchoMode.Password)
                if field.name == "google_client_secrets":
                    button = QPushButton("选择…")
                    button.clicked.connect(lambda _=False, w=widget: self.choose_file(w))
                    row = QWidget()
                    row_layout = QHBoxLayout(row)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    row_layout.addWidget(widget)
                    row_layout.addWidget(button)
                    form.addRow(labels[field.name], row)
                    self.inputs[field.name] = widget
                    continue
            form.addRow(labels[field.name], widget)
            self.inputs[field.name] = widget
        layout.addLayout(form)
        guide_url = "https://github.com/JackeyCloud/search-index-submitter/blob/main/docs/%E6%90%9C%E7%B4%A2%E5%BC%95%E6%93%8E%E4%B8%80%E9%94%AE%E6%8F%90%E4%BA%A4%E5%B7%A5%E5%85%B7_%E7%94%A8%E6%88%B7%E9%85%8D%E7%BD%AE%E4%B8%8E%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md"
        docs = QLabel(f'<a style="color:#68a7ff" href="{guide_url}">打开完整凭据申请与配置指南</a>')
        docs.setOpenExternalLinks(True)
        layout.addWidget(docs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose_file(self, widget: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择 OAuth 客户端 JSON", "", "JSON (*.json)")
        if path:
            widget.setText(path)

    def accept(self) -> None:
        for name, widget in self.inputs.items():
            setattr(self.config, name, widget.value() if isinstance(widget, QSpinBox) else widget.text().strip())
        self.config.save()
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = AppConfig.load()
        self.thread: QThread | None = None
        self.worker: SubmissionWorker | None = None
        self.setWindowTitle("新站搜索引擎一键提交")
        self.resize(1180, 820)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 22, 28, 24)
        outer.setSpacing(16)

        top = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("新站一键提交")
        title.setObjectName("Title")
        subtitle = QLabel("统一通知搜索引擎发现你的 URL 和 Sitemap，不承诺平台一定收录")
        subtitle.setObjectName("Subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        top.addLayout(heading)
        top.addStretch()
        config_button = QPushButton("平台凭据")
        config_button.clicked.connect(self.open_config)
        top.addWidget(config_button)
        outer.addLayout(top)

        input_card = QFrame()
        input_card.setObjectName("Card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(18, 16, 18, 18)
        section = QLabel("批量输入域名或网址")
        section.setObjectName("Section")
        input_layout.addWidget(section)
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("每行一个，例如：\nexample.com\nhttps://www.example.org/\nhttps://shop.example.net/products/new")
        self.input_box.setMinimumHeight(145)
        input_layout.addWidget(self.input_box)
        sitemap_row = QHBoxLayout()
        sitemap_label = QLabel("Sitemap")
        sitemap_label.setFixedWidth(72)
        self.sitemap_input = QLineEdit()
        self.sitemap_input.setPlaceholderText("留空自动发现；或使用 https://{host}/sitemap.xml")
        sitemap_row.addWidget(sitemap_label)
        sitemap_row.addWidget(self.sitemap_input)
        input_layout.addLayout(sitemap_row)
        outer.addWidget(input_card)

        platform_card = QFrame()
        platform_card.setObjectName("Card")
        platform_layout = QVBoxLayout(platform_card)
        platform_layout.setContentsMargins(18, 14, 18, 16)
        platform_layout.addWidget(QLabel("提交平台", objectName="Section"))
        platform_row = QHBoxLayout()
        self.checkboxes: dict[str, QCheckBox] = {}
        for provider_id, label, tooltip in PROVIDERS:
            checkbox = QCheckBox(label)
            checkbox.setToolTip(tooltip)
            checkbox.setChecked(provider_id in {"indexnow", "baidu", "google", "bing", "yandex"})
            self.checkboxes[provider_id] = checkbox
            platform_row.addWidget(checkbox)
        platform_row.addStretch()
        platform_layout.addLayout(platform_row)
        self.deduplicate_check = QCheckBox("提交前查重，已确认收录的 URL 自动跳过")
        self.deduplicate_check.setChecked(True)
        self.deduplicate_check.setToolTip("Google/Bing 使用站长 API 精确查询；无法确认的平台仍会提交")
        platform_layout.addWidget(self.deduplicate_check)
        outer.addWidget(platform_card)

        action_row = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("Subtitle")
        action_row.addWidget(self.status_label)
        action_row.addStretch()
        self.preview_button = QPushButton("预检")
        self.preview_button.setObjectName("Preview")
        self.preview_button.clicked.connect(lambda: self.start_submission(True))
        self.submit_button = QPushButton("开始一键提交")
        self.submit_button.setObjectName("Primary")
        self.submit_button.clicked.connect(lambda: self.start_submission(False))
        action_row.addWidget(self.preview_button)
        action_row.addWidget(self.submit_button)
        outer.addLayout(action_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["状态", "平台", "站点", "结果"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        outer.addWidget(self.table, 1)

    def open_config(self) -> None:
        ConfigDialog(self.config, self).exec()

    def selected_providers(self) -> list[str]:
        return [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]

    def start_submission(self, dry_run: bool) -> None:
        text = self.input_box.toPlainText().strip()
        providers = self.selected_providers()
        if not text:
            QMessageBox.warning(self, "缺少网址", "请至少输入一个域名或网址。")
            return
        if not providers:
            QMessageBox.warning(self, "缺少平台", "请至少选择一个提交平台。")
            return
        try:
            target_count = len(parse_targets(text, self.sitemap_input.text().strip()))
        except ValueError as exc:
            QMessageBox.warning(self, "输入有误", str(exc))
            return
        if not dry_run:
            answer = QMessageBox.question(self, "确认提交", f"将向 {len(providers)} 个平台处理 {target_count} 个站点。继续吗？")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.table.setRowCount(0)
        self.set_busy(True, "正在预检…" if dry_run else "正在提交…")
        self.thread = QThread(self)
        self.worker = SubmissionWorker(text, self.sitemap_input.text().strip(), providers, self.config, dry_run, self.deduplicate_check.isChecked())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.add_result)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.finish_submission)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def add_result(self, result: SubmissionResult) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        labels = {"success": "成功", "failed": "失败", "skipped": "跳过", "manual": "人工", "dry_run": "预检"}
        colors = {"success": "#55d6a7", "failed": "#ff718b", "skipped": "#f2c86b", "manual": "#c196ff", "dry_run": "#67a9ff"}
        values = [labels[result.status.value], result.provider, result.target, result.message]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column == 0:
                item.setForeground(QColor(colors[result.status.value]))
                item.setFont(QFont(item.font().family(), -1, QFont.Weight.DemiBold))
            self.table.setItem(row, column, item)

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "执行失败", message)

    def finish_submission(self) -> None:
        self.set_busy(False, f"完成，共 {self.table.rowCount()} 条结果")
        self.worker = None
        self.thread = None

    def set_busy(self, busy: bool, message: str) -> None:
        self.preview_button.setDisabled(busy)
        self.submit_button.setDisabled(busy)
        self.status_label.setText(message)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("新站搜索引擎一键提交")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
