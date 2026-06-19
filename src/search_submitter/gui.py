from __future__ import annotations

import sys
from dataclasses import fields
from datetime import datetime
from pathlib import Path

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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import AppConfig
from .engine import run_submissions
from .history import HistoryStore
from .index_check import refresh_index_statuses
from .models import IndexCheck, IndexState, SubmissionResult
from .targets import parse_targets


APP_STYLE = """
QWidget { background: #f6f9fe; color: #172033; font-size: 14px; }
QMainWindow { background: #f6f9fe; }
QFrame#Card { background: #ffffff; border: 1px solid #dce6f2; border-radius: 14px; }
QFrame#Hero { background: #eaf4ff; border: 1px solid #bfdcff; border-radius: 14px; }
QLabel#Title { font-size: 28px; font-weight: 700; color: #172033; }
QLabel#HeroTitle { font-size: 18px; font-weight: 700; color: #1459a8; }
QLabel#Subtitle { color: #64748b; font-size: 13px; }
QLabel#Section { font-size: 16px; font-weight: 650; color: #25324a; }
QTextEdit, QLineEdit, QSpinBox { background: #f8fafc; color: #172033; border: 1px solid #cbd8e8; border-radius: 8px; padding: 9px; selection-background-color: #2475e8; }
QTextEdit:focus, QLineEdit:focus { border: 1px solid #4b96ff; }
QPushButton { background: #eef4fb; color: #334155; border: 1px solid #cbd8e8; border-radius: 8px; padding: 9px 16px; font-weight: 600; }
QPushButton:hover { background: #e2edf9; }
QPushButton#Primary { background: #2475e8; border-color: #2475e8; color: white; }
QPushButton#Primary:hover { background: #1767d4; }
QPushButton#Preview { background: #ecfdf5; border-color: #9edfc6; color: #16785c; }
QPushButton:disabled { color: #94a3b8; background: #edf2f7; }
QCheckBox { spacing: 7px; color: #334155; }
QTabWidget::pane { border: 1px solid #dce6f2; background: #ffffff; border-radius: 8px; }
QTabBar::tab { background: #eaf0f8; color: #52637a; padding: 9px 18px; border: 1px solid #dce6f2; }
QTabBar::tab:selected { background: #ffffff; color: #1767d4; font-weight: 650; }
QTableWidget { background: #ffffff; alternate-background-color: #f7faff; border: 1px solid #dce6f2; border-radius: 9px; gridline-color: #e8eef6; }
QHeaderView::section { background: #edf3fb; color: #52637a; padding: 8px; border: 0; border-right: 1px solid #dce6f2; font-weight: 600; }
QToolTip { background: #ffffff; color: #172033; border: 1px solid #b8c7da; }
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
    completed = Signal(object)
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
            results = run_submissions(
                targets,
                self.providers,
                self.config,
                dry_run=self.dry_run,
                check_existing=self.check_existing,
                callback=self.result.emit,
            )
            self.completed.emit(results)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class RefreshWorker(QObject):
    progress = Signal(str, str, object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, urls: list[str], config: AppConfig):
        super().__init__()
        self.urls = urls
        self.config = config

    def run(self) -> None:
        try:
            refresh_index_statuses(
                self.urls,
                ("google", "bing"),
                self.config,
                callback=self.progress.emit,
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
        hint = QLabel("不需要填写平台账号密码。按下方教程登录官方平台获取 Key/token；Google 首次使用会打开官方 OAuth 授权页。凭据仅保存在本机。")
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
        docs = QLabel(f'<a style="color:#1767d4" href="{guide_url}">打开完整凭据申请与配置指南</a>')
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
        self.history_store = HistoryStore()
        self.thread: QThread | None = None
        self.worker: QObject | None = None
        self.refresh_done = 0
        self.setWindowTitle("内容收录助手")
        self.resize(1180, 820)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 22, 28, 24)
        outer.setSpacing(16)

        top = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("内容收录助手")
        title.setObjectName("Title")
        subtitle = QLabel("让你发布在自有网站上的内容，更快被搜索引擎发现")
        subtitle.setObjectName("Subtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        top.addLayout(heading)
        top.addStretch()
        self.refresh_button = QPushButton("⟳ 刷新收录")
        self.refresh_button.setToolTip("重新查询历史网址在 Google 和 Bing 的收录状态")
        self.refresh_button.clicked.connect(self.start_history_refresh)
        top.addWidget(self.refresh_button)
        config_button = QPushButton("账号与平台")
        config_button.clicked.connect(self.open_config)
        top.addWidget(config_button)
        outer.addLayout(top)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 14, 18, 14)
        hero_title = QLabel("把重复的站长平台提交，变成一次粘贴、一次检查、一次提交")
        hero_title.setObjectName("HeroTitle")
        hero_layout.addWidget(hero_title)
        hero_copy = QLabel("适合已验证的官网、博客、产品页和内容站点。自动提取链接，提交前查重，并持续记录 Google、百度、Bing、Yandex 等平台状态。")
        hero_copy.setObjectName("Subtitle")
        hero_copy.setWordWrap(True)
        hero_layout.addWidget(hero_copy)
        steps = QLabel("① 粘贴网址或分享文案    ② 连接站长平台    ③ 查重并提交")
        steps.setStyleSheet("color:#1767d4;font-weight:650;padding-top:4px;")
        hero_layout.addWidget(steps)
        ownership = QLabel("提示：小红书、携程等第三方页面可提取链接和保存记录，但不能用你的站长凭据代替平台所有者提交。")
        ownership.setWordWrap(True)
        ownership.setStyleSheet("color:#8a5a12;background:#fff7e6;border:1px solid #f2d39b;border-radius:7px;padding:7px;")
        hero_layout.addWidget(ownership)
        outer.addWidget(hero)

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
        self.config_hint = QLabel()
        self.config_hint.setWordWrap(True)
        self.config_hint.setStyleSheet("background:#eaf4ff;color:#1767d4;border:1px solid #9cc8f7;border-radius:8px;padding:9px;")
        self.config_hint.setToolTip("点击打开账号与平台配置")
        self.config_hint.mousePressEvent = lambda _event: self.open_config()
        platform_layout.addWidget(self.config_hint)
        for checkbox in self.checkboxes.values():
            checkbox.toggled.connect(self.update_config_hint)
        self.update_config_hint()
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

        self.tabs = QTabWidget()
        self.history_table = QTableWidget(0, 9)
        self.history_table.setHorizontalHeaderLabels(["提交时间", "网址", "G", "百度", "Bing", "Yandex", "360", "神马", "最近检查"])
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        history_header = self.history_table.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, 8):
            history_header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.tabs.addTab(self.history_table, "提交记录")

        self.result_table = QTableWidget(0, 4)
        self.result_table.setHorizontalHeaderLabels(["状态", "平台", "站点", "结果"])
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.verticalHeader().setVisible(False)
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.result_table, "本次结果")
        outer.addWidget(self.tabs, 1)
        self.load_history()

    def open_config(self) -> None:
        if ConfigDialog(self.config, self).exec() == QDialog.DialogCode.Accepted:
            self.update_config_hint()

    def missing_credentials(self, providers: list[str] | None = None) -> list[str]:
        providers = providers or self.selected_providers()
        missing = []
        if "indexnow" in providers and not self.config.indexnow_key.strip():
            missing.append("IndexNow Key 与网站根目录 Key 文件")
        if "baidu" in providers and not (self.config.baidu_token.strip() or self.config.baidu_token_map.strip()):
            missing.append("百度搜索资源平台 token")
        if "google" in providers:
            path = Path(self.config.google_client_secrets).expanduser() if self.config.google_client_secrets else None
            if not path or not path.exists():
                missing.append("Google OAuth 客户端 JSON")
        if "bing" in providers and not self.config.bing_api_key.strip():
            missing.append("Bing Webmaster API Key")
        if "yandex" in providers and not self.config.yandex_oauth_token.strip():
            missing.append("Yandex OAuth Token")
        return missing

    def update_config_hint(self) -> None:
        missing = self.missing_credentials()
        if missing:
            self.config_hint.setText(f"还差 {len(missing)} 项配置 · 点击这里按教程完成。软件不会要求平台密码。")
            self.config_hint.setStyleSheet("background:#eaf4ff;color:#1767d4;border:1px solid #9cc8f7;border-radius:8px;padding:9px;")
        else:
            self.config_hint.setText("✓ 已选平台配置完成，可以直接预检并提交")
            self.config_hint.setStyleSheet("background:#ecfdf5;color:#16785c;border:1px solid #9edfc6;border-radius:8px;padding:9px;")

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
        missing = self.missing_credentials(providers)
        if not dry_run and missing:
            message = "以下平台配置尚未完成：\n\n• " + "\n• ".join(missing)
            message += "\n\n只能提交您拥有或已验证的网站。是否先打开账号与平台配置？"
            answer = QMessageBox.question(self, "提交前还差一步", message)
            if answer == QMessageBox.StandardButton.Yes:
                self.open_config()
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
        targets = parse_targets(text, self.sitemap_input.text().strip())
        self.current_submission_urls = [url for target in targets for url in target.urls]
        self.result_table.setRowCount(0)
        self.tabs.setCurrentWidget(self.result_table)
        self.set_busy(True, "正在预检…" if dry_run else "正在提交…")
        self.thread = QThread(self)
        self.worker = SubmissionWorker(text, self.sitemap_input.text().strip(), providers, self.config, dry_run, self.deduplicate_check.isChecked())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.add_result)
        self.worker.completed.connect(lambda results: self.handle_submission_completed(results, dry_run))
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.finish_submission)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def add_result(self, result: SubmissionResult) -> None:
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        labels = {"success": "成功", "failed": "失败", "skipped": "跳过", "manual": "人工", "dry_run": "预检"}
        colors = {"success": "#55d6a7", "failed": "#ff718b", "skipped": "#f2c86b", "manual": "#c196ff", "dry_run": "#67a9ff"}
        values = [labels[result.status.value], result.provider, result.target, result.message]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column == 0:
                item.setForeground(QColor(colors[result.status.value]))
                item.setFont(QFont(item.font().family(), -1, QFont.Weight.DemiBold))
            self.result_table.setItem(row, column, item)

    def handle_submission_completed(self, results: list[SubmissionResult], dry_run: bool) -> None:
        if not dry_run:
            self.history_store.record_submission(self.current_submission_urls, results)
            self.load_history()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "执行失败", message)

    def finish_submission(self) -> None:
        self.set_busy(False, f"完成，共 {self.result_table.rowCount()} 条结果")
        self.worker = None
        self.thread = None

    def start_history_refresh(self) -> None:
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, "任务进行中", "请等待当前任务完成后再刷新。")
            return
        records = self.history_store.list_records()
        if not records:
            QMessageBox.information(self, "暂无记录", "提交网址后会在这里保存永久记录。")
            return
        self.refresh_done = 0
        self.set_busy(True, f"正在刷新 {len(records)} 个网址…")
        self.thread = QThread(self)
        self.worker = RefreshWorker([record.url for record in records], self.config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.handle_refresh_result)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.finish_history_refresh)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def handle_refresh_result(self, url: str, provider_id: str, check: IndexCheck) -> None:
        self.history_store.update_index_status(url, provider_id, check.state)
        self.refresh_done += 1
        self.status_label.setText(f"已检查 {self.refresh_done} 项：{provider_id} · {check.message}")

    def finish_history_refresh(self) -> None:
        self.load_history()
        self.tabs.setCurrentWidget(self.history_table)
        self.set_busy(False, f"刷新完成，共检查 {self.refresh_done} 项")
        self.worker = None
        self.thread = None

    def load_history(self) -> None:
        records = self.history_store.list_records()
        self.history_table.setRowCount(len(records))
        platform_columns = {"google": 2, "baidu": 3, "bing": 4, "yandex": 5, "360": 6, "shenma": 7}
        brand_colors = {
            "google": "#4285f4", "baidu": "#4e6ef2", "bing": "#00a4ef",
            "yandex": "#ff4b4b", "360": "#35c759", "shenma": "#ff7a1a",
        }
        for row, record in enumerate(records):
            date_item = QTableWidgetItem(self.format_date(record.last_submitted_at))
            date_item.setToolTip(f"首次：{record.first_submitted_at}\n提交次数：{record.submission_count}")
            self.history_table.setItem(row, 0, date_item)
            url_item = QTableWidgetItem(record.url)
            url_item.setToolTip(record.url)
            self.history_table.setItem(row, 1, url_item)
            for provider_id, column in platform_columns.items():
                state = record.index_statuses.get(provider_id, IndexState.UNKNOWN.value)
                icon = "●" if state == IndexState.INDEXED.value else "○"
                item = QTableWidgetItem(icon)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if state == IndexState.INDEXED.value:
                    item.setForeground(QColor(brand_colors[provider_id]))
                    item.setToolTip("已确认收录")
                elif state == IndexState.NOT_INDEXED.value:
                    item.setForeground(QColor("#f2c86b"))
                    item.setToolTip("查询时暂未确认收录")
                else:
                    item.setForeground(QColor("#64748b"))
                    submitted = provider_id in record.submitted_providers
                    item.setToolTip("已提交，尚无法确认收录" if submitted else "尚无收录数据")
                self.history_table.setItem(row, column, item)
            checked_item = QTableWidgetItem(self.format_date(record.last_checked_at) if record.last_checked_at else "未刷新")
            self.history_table.setItem(row, 8, checked_item)
        self.tabs.setTabText(0, f"提交记录 ({len(records)})")

    @staticmethod
    def format_date(value: str | None) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).strftime("%m-%d %H:%M")
        except ValueError:
            return value

    def set_busy(self, busy: bool, message: str) -> None:
        self.preview_button.setDisabled(busy)
        self.submit_button.setDisabled(busy)
        self.refresh_button.setDisabled(busy)
        self.status_label.setText(message)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("内容收录助手")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
