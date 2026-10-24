from __future__ import annotations
import json, os, sys, zipfile, platform, struct
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, QPointF, QLocale, QTimer
from PySide6.QtGui import QPixmap, QAction, QImage, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QSizePolicy, QStackedWidget,
    QPushButton, QLabel, QComboBox, QSlider, QFileDialog, QMessageBox, QScrollArea, QCheckBox,
    QSpinBox, QGroupBox, QSplitter, QProgressDialog, QInputDialog)
from .engine import DEVICE_PROFILES, OUTPUT_MODES, render_image, four_level_dither, histogram_data

APP_NAME = "EInkXT Wallpaper Studio"
APP_VERSION = "0.5.0"
PROJECT_WEBSITE = "https://evoll.github.io/EInkXTWallpaperStudio/"
PROJECT_REPOSITORY = "https://github.com/evoll/EInkXTWallpaperStudio"
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff *.gif)"


def resource_path(relative_path: str) -> Path:
    """Resolve bundled resources both in source runs and PyInstaller builds."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return bundle_root / relative_path

PRESETS = {
    "Custom": {},
    "Photo (balanced)": {"brightness": 0, "contrast": 12, "gamma": 100, "sharpness": 35, "noise_reduction": 5},
    "Portrait / faces": {"brightness": 4, "contrast": 5, "gamma": 108, "sharpness": 12, "noise_reduction": 20},
    "Landscape / scenery": {"brightness": 0, "contrast": 24, "gamma": 95, "sharpness": 55, "noise_reduction": 0},
    "Punchy B&W": {"brightness": 0, "contrast": 45, "gamma": 100, "sharpness": 45, "noise_reduction": 0},
    "Line art / manga": {"brightness": 0, "contrast": 60, "gamma": 100, "sharpness": 80, "noise_reduction": 0},
    "Text / screenshot": {"brightness": 0, "contrast": 35, "gamma": 100, "sharpness": 25, "noise_reduction": 0},
    "Soft / faded": {"brightness": 6, "contrast": -18, "gamma": 115, "sharpness": 0, "noise_reduction": 25},
}

# English is the canonical translation key language; combo-box user data keeps processing values stable.
TRANSLATIONS = {
    "Файл":"File", "Открыть…":"Open…", "Сохранить проект…":"Save project…", "Загрузить проект…":"Load project…",
    "Пакетная обработка…":"Batch processing…", "Выход":"Exit", "Вид":"View", "Опции":"Options", "О программе":"About", "Переключить светлую/тёмную тему":"Toggle light/dark theme",
    "Открыть изображение":"Open image", "＋  Open image":"＋  Open image", "Режим экрана /\nвывода":"Output mode /\nformat", "Устройство и кадрирование":"Device & framing", "Профиль":"Profile", "Свои размеры":"Custom size",
    "Ширина":"Width", "Высота":"Height", "Ориентация":"Orientation", "Портрет":"Portrait", "Альбомная":"Landscape",
    "Масштабирование":"Fit mode", "Повернуть 90°":"Rotate 90°", "Центрировать":"Center crop", "Сбросить кадрирование":"Reset framing", "Обработка":"Adjustments",
    "Масштаб, %":"Zoom, %", "Яркость":"Brightness", "Контраст":"Contrast", "Гамма, %":"Gamma, %", "Резкость":"Sharpness",
    "Подавление шума":"Noise reduction", "Пресет":"Preset", "Пользовательский":"Custom", "Фото":"Photo", "Текст / графика":"Text / graphics",
    "Мягкий":"Soft", "Портрет":"Portrait", "Дизеринг":"Dithering", "4 уровня серого":"4 gray levels", "Сбросить обработку":"Reset adjustments",
    "Экспорт и проект":"Export & project", "Экспорт BMP (24-bit)":"Export BMP (24-bit)", "Экспорт PNG (4 уровня серого)":"Export PNG (4 gray levels)", "Экспорт PNG (выбранный режим)":"Export PNG (selected output mode)",
    "Пакетная обработка изображений…":"Batch process images…", "Сохранить проект (.xtws)…":"Save project (.xtws)…",
    "Экспорт изображения":"Export image", "Пресет":"Preset", "Экспорт BMP (24-bit)":"Export BMP (selected output mode)",
    "Экспорт PNG (выбранный режим)":"Export PNG (selected output mode)", "Формат экспорта":"Export format",
    "ПРЕДПРОСМОТР РЕЗУЛЬТАТА":"OUTPUT PREVIEW", "Гистограмма":"Histogram", "Откройте изображение или перетащите файл в окно":"Open an image or drag a file into the window",
    "Cover":"Cover", "Fit (white bars)":"Fit (white bars)", "Fit (black bars)":"Fit (black bars)", "Floyd–Steinberg":"Floyd–Steinberg",
    "Atkinson":"Atkinson", "Bayer 4×4":"Bayer 4×4", "Jarvis–Judice–Ninke":"Jarvis–Judice–Ninke", "Stucki":"Stucki", "Burkes":"Burkes", "None":"None",
    "Авто":"Auto", "Русский":"Russian", "Английский":"English", "Язык":"Language", "Локальная обработка — изображения не отправляются в сеть":"Local processing — images are never uploaded",
    "Открыть изображение":"Open image", "Enable crop / framing":"Enable crop / framing", "Сначала откройте изображение.":"Open an image first.", "Экспорт":"Export", "Ошибка открытия":"Open error",
    "Не удалось открыть файл:\n":"Could not open file:\n", "Ошибка экспорта":"Export error", "Сохранено: ":"Saved: ",
    "Сохранить проект":"Save project", "Загрузить проект":"Load project", "Ошибка проекта":"Project error", "Выберите изображения для пакетной обработки":"Select images for batch processing",
    "Папка для результатов":"Output folder", "Формат экспорта":"Export format", "Формат":"Format", "PNG":"PNG", "BMP":"BMP",
    "Обработка изображений…":"Processing images…", "Отмена":"Cancel", "Пакетная обработка":"Batch processing", "Успешно обработано: ":"Processed successfully: ",
    " из ":" of ", "Папка: ":"Folder: ", "\n\nОшибки:\n":"\n\nErrors:\n", "Ошибка обработки: ":"Processing error: ",
}
LANGUAGE_ROLE = Qt.ItemDataRole.UserRole + 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"{APP_NAME} {APP_VERSION}"); self.resize(1280, 850); self.setMinimumSize(1000, 620); self.language_mode = "auto"; self.language = "en"; self.language_code = "en"; self.translations = {}; self.language_files = self._load_language_files(); self.theme_mode = "system"
        self.source = None; self.source_path = None; self.rotation = 0; self.offset_x = 0.; self.offset_y = 0.; self.drag_pos = None
        self.last_render = None; self.dark = False; self.batch_files = []; self.crop_mode_enabled = False; self._refresh_timer = QTimer(self); self._refresh_timer.setSingleShot(True); self._refresh_timer.setInterval(90); self._refresh_timer.timeout.connect(self._render_preview)
        self._build_ui(); self._theme(); self._set_combo_language_data(); self.apply_language(); self.statusBar().showMessage(self.tr_text("Локальная обработка — изображения не отправляются в сеть"))

    def _build_ui(self):
        file_menu = self.menuBar().addMenu("Файл"); self.file_menu = file_menu
        for label, callback, shortcut in [("Открыть…", self.open_image, "Ctrl+O"), ("Сохранить проект…", self.save_project, "Ctrl+S"), ("Загрузить проект…", self.load_project, "Ctrl+Shift+O"), ("Пакетная обработка…", self.batch_export, "Ctrl+B"), ("Выход", self.close, "Ctrl+Q")]:
            action = QAction(label, self); action.triggered.connect(callback)
            if shortcut: action.setShortcut(shortcut)
            file_menu.addAction(action)
        view_menu = self.menuBar().addMenu("Опции"); self.view_menu = view_menu
        theme_action = QAction("Переключить светлую/тёмную тему", self); theme_action.triggered.connect(self.toggle_theme); view_menu.addAction(theme_action); self.theme_action = theme_action
        view_menu.addSeparator(); self.about_action = QAction("О программе", self); self.about_action.triggered.connect(self.show_about); view_menu.addAction(self.about_action)
        self.language_widget = QWidget(); language_layout = QHBoxLayout(self.language_widget); language_layout.setContentsMargins(8, 0, 4, 0); language_layout.setSpacing(5)
        self.language_label = QLabel("Язык:"); language_layout.addWidget(self.language_label)
        self.language_combo = QComboBox(); self.language_combo.setMinimumWidth(105); language_layout.addWidget(self.language_combo)
        self._populate_language_combo(); self.language_combo.currentIndexChanged.connect(self.language_changed)
        self.menuBar().setCornerWidget(self.language_widget)
        central = QWidget(); central_layout = QVBoxLayout(central); central_layout.setContentsMargins(6, 0, 6, 6); central_layout.setSpacing(2)
        splitter = QSplitter(); central_layout.addWidget(splitter, 1); self.setCentralWidget(central)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(420)
        scroll.setMaximumWidth(430)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        panel = QWidget()
        panel.setMinimumSize(0, 0)
        panel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        panel.setMaximumWidth(420)
        scroll.setWidget(panel)
        root = QVBoxLayout(panel)
        root.setContentsMargins(6, 5, 6, 5)
        root.setSpacing(6)
        splitter.addWidget(scroll)
        device_group = QGroupBox("Устройство и кадрирование"); form = QFormLayout(device_group); form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow); form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows); form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter); form.setHorizontalSpacing(6); form.setVerticalSpacing(6)
        self.device = QComboBox(); self.device.setMaximumWidth(300); self.device.addItems(DEVICE_PROFILES); self.device.currentIndexChanged.connect(self.device_changed); form.addRow("Профиль", self.device)
        customrow = QHBoxLayout(); customrow.setContentsMargins(0, 0, 0, 0); customrow.setSpacing(4); self.custom_w = QSpinBox(); self.custom_w.setRange(64, 3000); self.custom_w.setValue(528); self.custom_w.setMinimumWidth(58); self.custom_w.setMaximumWidth(86); self.custom_h = QSpinBox(); self.custom_h.setRange(64, 4000); self.custom_h.setValue(792); self.custom_h.setMinimumWidth(58); self.custom_h.setMaximumWidth(86)
        self.custom_w.valueChanged.connect(self.refresh); self.custom_h.valueChanged.connect(self.refresh); customrow.addWidget(QLabel("Width")); customrow.addWidget(self.custom_w, 1); customrow.addWidget(QLabel("Height")); customrow.addWidget(self.custom_h, 1); form.addRow("Custom size", customrow)
        self.orientation = QComboBox(); self.orientation.setMaximumWidth(300); self.orientation.addItems(["Портрет", "Альбомная"]); self.orientation.currentIndexChanged.connect(self.refresh); form.addRow("Ориентация", self.orientation)
        self.fit = QComboBox(); self.fit.setMaximumWidth(300); self.fit.addItems(["Cover", "Fit (white bars)", "Fit (black bars)"]); self.fit.currentIndexChanged.connect(self.refresh); form.addRow("Масштабирование", self.fit)
        row = QHBoxLayout(); rot = QPushButton("↻ Повернуть 90°"); rot.clicked.connect(self.rotate); center = QPushButton("Центрировать"); center.clicked.connect(self.center_crop); row.addWidget(rot); row.addWidget(center); form.addRow(row); reset_frame = QPushButton("Сбросить кадрирование"); reset_frame.clicked.connect(self.reset_framing); form.addRow(reset_frame); self.crop_mode = QCheckBox("Enable crop / framing"); self.crop_mode.setChecked(False); self.crop_mode.toggled.connect(self.set_crop_mode); form.addRow(self.crop_mode); root.addWidget(device_group)
        adjust = QGroupBox("Обработка"); af = QFormLayout(adjust)
        self.sliders = {}
        for key, title, low, high, default in [("zoom","Масштаб, %",50,400,100),("brightness","Яркость",-100,100,0),("contrast","Контраст",-100,100,0),("gamma","Гамма, %",30,300,100),("sharpness","Резкость",0,150,0),("noise_reduction","Подавление шума",0,100,0)]:
            s = QSlider(Qt.Orientation.Horizontal); s.setRange(low, high); s.setValue(default); s.valueChanged.connect(self.refresh); self.sliders[key] = s
            label = QLabel(str(default)); s.valueChanged.connect(lambda v, l=label: l.setText(str(v)))
            line = QHBoxLayout(); line.addWidget(s, 1); line.addWidget(label); af.addRow(title, line)
        self.preset = QComboBox(); self.preset.setMaximumWidth(300); self.preset.addItems(PRESETS); self.preset.setCurrentIndex(list(PRESETS).index("Photo (balanced)")); self.preset.currentTextChanged.connect(self.apply_preset); af.addRow("Preset", self.preset)
        self.dither = QComboBox(); self.dither.setMaximumWidth(300); self.dither.addItems(["Atkinson", "Floyd–Steinberg", "Bayer 4×4", "Jarvis–Judice–Ninke", "Stucki", "Burkes", "None"]); self.dither.currentTextChanged.connect(self.refresh); af.addRow("Дизеринг", self.dither)
        self.output_mode = QComboBox(); self.output_mode.setMaximumWidth(300); self.output_mode.addItems(list(OUTPUT_MODES)); self.output_mode.currentTextChanged.connect(self.refresh); self.output_mode_label = QLabel("Режим экрана /\nвывода"); self.output_mode_label.setWordWrap(True); af.addRow(self.output_mode_label, self.output_mode)
        reset = QPushButton("Сбросить обработку"); reset.clicked.connect(self.reset_adjustments); af.addRow(reset); root.addWidget(adjust)
        out_group = QGroupBox("Экспорт и проект"); of = QVBoxLayout(out_group)
        bmp = QPushButton("Export BMP (selected output mode)"); bmp.clicked.connect(lambda: self.export_one("BMP")); of.addWidget(bmp)
        png = QPushButton("Export PNG (selected output mode)"); png.clicked.connect(lambda: self.export_one("PNG")); of.addWidget(png)
        pxc = QPushButton("Export PXC (CrossPoint 2bpp)"); pxc.clicked.connect(lambda: self.export_one("PXC")); of.addWidget(pxc)
        batch = QPushButton("Batch process images…"); batch.clicked.connect(self.batch_export); of.addWidget(batch)
        savep = QPushButton("Сохранить проект (.xtws)…"); savep.clicked.connect(self.save_project); of.addWidget(savep); root.addWidget(out_group); root.addStretch()
        right = QWidget(); rv = QVBoxLayout(right); heading = QHBoxLayout(); heading.addWidget(QLabel("ПРЕДПРОСМОТР РЕЗУЛЬТАТА")); heading.addStretch()
        self.hist_check = QCheckBox("Гистограмма"); self.hist_check.stateChanged.connect(self.refresh); heading.addWidget(self.hist_check); rv.addLayout(heading)
        self.preview_stack = QStackedWidget()
        empty = QWidget(); empty_layout = QVBoxLayout(empty); empty_layout.addStretch(1)
        self.empty_prompt = QLabel("Open an image from File menu, or click below"); self.empty_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter); empty_layout.addWidget(self.empty_prompt)
        self.empty_open_btn = QPushButton("＋  Open image"); self.empty_open_btn.setMaximumWidth(260); self.empty_open_btn.clicked.connect(self.open_image); empty_layout.addWidget(self.empty_open_btn, 0, Qt.AlignmentFlag.AlignHCenter); empty_layout.addStretch(1)
        self.preview_stack.addWidget(empty)
        self.preview = QLabel(); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumSize(160, 180); self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored); self.preview.setStyleSheet("border:1px solid #525966;border-radius:12px;")
        self.preview.mousePressEvent = self.mouse_down; self.preview.mouseMoveEvent = self.mouse_move; self.preview.mouseReleaseEvent = self.mouse_up; self.preview.wheelEvent = self.wheel
        self.preview_stack.addWidget(self.preview); self.preview_stack.setCurrentWidget(empty)
        rv.addWidget(self.preview_stack, 1); self.histogram = QLabel(); self.histogram.setFixedHeight(95); self.histogram.setAlignment(Qt.AlignmentFlag.AlignCenter); rv.addWidget(self.histogram); self.histogram.hide(); splitter.addWidget(right); splitter.setChildrenCollapsible(False); splitter.setSizes([420, 830]); splitter.setStretchFactor(0, 0); splitter.setStretchFactor(1, 1); splitter.setHandleWidth(5)
        self.setAcceptDrops(True)

    def _load_language_files(self):
        """Load optional JSON translations from source-root lang/ or package lang/."""
        roots = [Path(__file__).resolve().parents[2] / "lang", Path(sys.executable).resolve().parent / "lang", Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)) / "lang"]
        found = {}
        for root in roots:
            if root.is_dir():
                for path in root.glob("*.json"):
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        if isinstance(data, dict): found[path.stem.lower()] = data
                    except Exception:
                        pass
        return found

    def _populate_language_combo(self):
        choices = [("auto", "Авто"), ("ru", "Русский"), ("en", "Английский")]
        for code in sorted(self.language_files):
            if code not in {"ru", "en"}:
                choices.append((code, self.language_files[code].get("__language_name__", code)))
        self.language_combo.blockSignals(True); self.language_combo.clear()
        for code, label in choices: self.language_combo.addItem(label, code)
        self.language_combo.setCurrentIndex(0); self.language_combo.blockSignals(False)

    def tr_text(self, text):
        # English is the canonical source language. Older Russian call sites are
        # mapped to English keys for backwards-compatible projects.
        source_to_english = {source: target for source, target in TRANSLATIONS.items()}
        key = source_to_english.get(text, text)
        custom = self.language_files.get(self.language, {})
        if key in custom:
            return custom[key]
        if self.language == "en":
            return key
        # A missing translation falls back to the canonical English source string.
        return key

    def _set_combo_language_data(self):
        for combo in self.findChildren(QComboBox):
            if combo is self.language_combo: continue
            for i in range(combo.count()): combo.setItemData(i, combo.itemText(i), LANGUAGE_ROLE)

    def combo_value(self, combo):
        value = combo.currentData(LANGUAGE_ROLE)
        return value if value is not None else combo.currentText()

    def set_combo_value(self, combo, value):
        for i in range(combo.count()):
            canonical = combo.itemData(i, LANGUAGE_ROLE)
            if canonical == value or combo.itemText(i) == value:
                combo.setCurrentIndex(i); return
        combo.setCurrentText(value)

    def language_changed(self, index):
        code = self.language_combo.currentData()
        self.language_mode = code or "auto"
        self.apply_language()

    def apply_language(self):
        if self.language_mode == "auto":
            locale_name = QLocale.system().name().lower(); short = locale_name.split("_")[0]
            self.language = short if short in self.language_files and short not in ("ru", "en") else ("ru" if short == "ru" else "en")
        else: self.language = self.language_mode
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        for widget in self.findChildren(QLabel):
            original = widget.property("i18n_original")
            if original is None: original = widget.text(); widget.setProperty("i18n_original", original)
            widget.setText(self.tr_text(original))
        for widget in self.findChildren(QPushButton):
            original = widget.property("i18n_original")
            if original is None: original = widget.text(); widget.setProperty("i18n_original", original)
            widget.setText(self.tr_text(original))
        for widget in self.findChildren(QGroupBox):
            original = widget.property("i18n_original")
            if original is None: original = widget.title(); widget.setProperty("i18n_original", original)
            widget.setTitle(self.tr_text(original))
        for widget in self.findChildren(QCheckBox):
            original = widget.property("i18n_original")
            if original is None: original = widget.text(); widget.setProperty("i18n_original", original)
            widget.setText(self.tr_text(original))
        for combo in self.findChildren(QComboBox):
            if combo is self.language_combo: continue
            for i in range(combo.count()):
                original = combo.itemData(i, LANGUAGE_ROLE)
                if original is not None: combo.setItemText(i, self.tr_text(original))
        for menu, original in [(self.file_menu, "Файл"), (self.view_menu, "Опции")]: menu.setTitle(self.tr_text(original))
        for action in self.file_menu.actions() + self.view_menu.actions():
            original = action.property("i18n_original")
            if original is None: original = action.text(); action.setProperty("i18n_original", original)
            action.setText(self.tr_text(original))
        self.language_label.setText(self.tr_text("Язык") + ":")
        labels = {"auto": self.tr_text("Авто"), "ru": self.tr_text("Русский"), "en": self.tr_text("Английский")}
        for i in range(self.language_combo.count()):
            code = self.language_combo.itemData(i)
            if code in labels: self.language_combo.setItemText(i, labels[code])
        self.statusBar().showMessage(self.tr_text("Локальная обработка — изображения не отправляются в сеть"))
        self.refresh()

    def _theme(self):
        if self.theme_mode == "system":
            self.setStyleSheet("")
            return
        if self.theme_mode == "dark":
            self.setStyleSheet("QMainWindow,QWidget{background:#171a20;color:#e7eaf0} QGroupBox{border:1px solid #414753;border-radius:8px;margin-top:10px;padding:8px;font-weight:600} QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px} QPushButton{background:#303744;border:1px solid #4c5667;border-radius:6px;padding:7px} QPushButton:hover{background:#3b4658} QComboBox,QSpinBox{background:#252a33;border:1px solid #454d5b;border-radius:4px;padding:4px} QSlider::groove:horizontal{height:5px;background:#424957} QSlider::handle:horizontal{background:#8bb8ff;width:13px;margin:-5px 0;border-radius:6px}")
        else:
            self.setStyleSheet("QGroupBox{border:1px solid #b9c0ca;border-radius:8px;margin-top:10px;padding:8px;font-weight:600} QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px} QPushButton{padding:7px;border:1px solid #c3c9d2;border-radius:5px} QComboBox,QSpinBox{padding:4px;border:1px solid #c3c9d2;border-radius:4px}")

    def toggle_theme(self):
        self.theme_mode = "dark" if self.theme_mode != "dark" else "light"
        self._theme()

    def show_about(self):
        lang = self.language
        if lang == "en":
            title, build, contacts = "About EInkXT Wallpaper Studio", "Build information", "Contacts"
            text = (f"<h2>{APP_NAME} {APP_VERSION}</h2>"
                    "<p>Application for preparing images for E-Ink displays.</p>"
                    f"<p><b>{build}:</b><br>Version: {APP_VERSION}<br>Python: {sys.version.split()[0]}<br>Qt: {__import__('PySide6').__version__}<br>Pillow: {Image.__version__ if hasattr(Image, '__version__') else 'installed'}<br>OS: {platform.platform()}<br>Architecture: {platform.machine()}</p>"
                    f"<p><b>{contacts}:</b><br>Website: <a href='{PROJECT_WEBSITE}'>{PROJECT_WEBSITE}</a><br>Repository: <a href='{PROJECT_REPOSITORY}'>{PROJECT_REPOSITORY}</a></p>"
                    "<p>Source code, releases and documentation are available from the project links above.</p>")
        else:
            title, build, contacts = "О программе EInkXT Wallpaper Studio", "Сведения о сборке", "Контакты"
            text = (f"<h2>{APP_NAME} {APP_VERSION}</h2>"
                    "<p>Приложение для подготовки изображений для E-Ink экранов.</p>"
                    f"<p><b>{build}:</b><br>Версия: {APP_VERSION}<br>Python: {sys.version.split()[0]}<br>Qt: {__import__('PySide6').__version__}<br>Pillow: установлен<br>ОС: {platform.platform()}<br>Архитектура: {platform.machine()}</p>"
                    f"<p><b>{contacts}:</b><br>Сайт: <a href='{PROJECT_WEBSITE}'>{PROJECT_WEBSITE}</a><br>Репозиторий: <a href='{PROJECT_REPOSITORY}'>{PROJECT_REPOSITORY}</a></p>"
                    "<p>Исходный код, релизы и документация доступны по ссылкам выше.</p>")
        box = QMessageBox(self); box.setWindowTitle(title); box.setTextFormat(Qt.TextFormat.RichText); box.setText(text); box.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction); box.setStandardButtons(QMessageBox.StandardButton.Ok); link_label = box.findChild(QLabel, "qt_msgbox_label"); link_label.setOpenExternalLinks(True) if link_label else None; box.exec()

    def current_size(self):
        if self.combo_value(self.device) == "Custom": w,h=self.custom_w.value(),self.custom_h.value()
        else: w,h=DEVICE_PROFILES[self.combo_value(self.device)]
        return (h,w) if self.orientation.currentIndex() else (w,h)
    def settings(self):
        return {"size":self.current_size(),"fit_mode":self.combo_value(self.fit),"rotation":self.rotation,"offset_x":self.offset_x,"offset_y":self.offset_y,"dither":self.combo_value(self.dither), "output_mode":self.combo_value(self.output_mode), **{k:s.value() for k,s in self.sliders.items()}}
    def open_image(self):
        path,_=QFileDialog.getOpenFileName(self,self.tr_text("Open image"), "", IMAGE_FILTER)
        if path: self.load_image(path)
    def load_image(self,path):
        try:
            self.source=Image.open(path).convert("RGB"); self.source_path=str(path); self.rotation=0; self.offset_x=self.offset_y=0; self.sliders["zoom"].setValue(100); self.refresh()
        except Exception as e: QMessageBox.critical(self,self.tr_text("Ошибка открытия"),self.tr_text("Не удалось открыть файл:\n") + str(e))
    def device_changed(self):
        if self.combo_value(self.device) != "Custom":
            w,h=DEVICE_PROFILES[self.combo_value(self.device)]; self.custom_w.blockSignals(True); self.custom_h.blockSignals(True); self.custom_w.setValue(w); self.custom_h.setValue(h); self.custom_w.blockSignals(False); self.custom_h.blockSignals(False)
        self.refresh()
    def rotate(self): self.rotation=(self.rotation+90)%360; self.refresh()
    def center_crop(self):
        """Center the image and reset zoom without changing rotation or fit mode."""
        self.offset_x = self.offset_y = 0
        self.sliders["zoom"].setValue(100)
        self.refresh()

    def reset_framing(self):
        """Restore the same framing defaults as the online editor reset button."""
        self.fit.setCurrentIndex(0)
        self.rotation = 0
        self.offset_x = self.offset_y = 0
        self.sliders["zoom"].setValue(100)
        self.refresh()
    def _apply_preset_baseline(self, name=None):
        """Apply a preset from neutral defaults so values from another preset cannot leak."""
        name = name or self.combo_value(self.preset)
        baseline = {"brightness": 0, "contrast": 0, "gamma": 100,
                    "sharpness": 0, "noise_reduction": 0}
        baseline.update(PRESETS.get(name, {}))
        for key, value in baseline.items():
            self.sliders[key].setValue(value)

    def reset_adjustments(self):
        # Keep the selected preset and restore its baseline, rather than switching
        # the preset selector to Custom or leaving values from another preset.
        selected_preset = self.combo_value(self.preset)
        self._apply_preset_baseline(selected_preset)
        # Processing reset must not alter framing, zoom, rotation, offsets, or dither.
        self.refresh()

    def apply_preset(self, name):
        name = self.combo_value(self.preset)
        self._apply_preset_baseline(name)
        self.refresh()
    def estimate_export_size(self, w, h):
        """Estimate default BMP export size for the selected output mode."""
        mode = self.combo_value(self.output_mode).lower()
        if "rgb" in mode or "kaleido" in mode:
            bpp = 24
            size = 54 + ((w * bpp + 31) // 32) * 4 * h
        elif "256" in mode or "spectra" in mode or "16" in mode:
            bpp = 8
            size = 54 + 256 * 4 + ((w * bpp + 31) // 32) * 4 * h
        else:
            # Four grayscale levels are stored as 4-bit indexed BMP.
            bpp = 4
            size = 54 + 16 * 4 + ((w * bpp + 31) // 32) * 4 * h
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MiB"
        if size >= 1024:
            return f"{size / 1024:.1f} KiB"
        return f"{size} B"

    def refresh(self, *_):
        """Debounce UI events; preview intentionally skips expensive error-diffusion.

        Full-quality dithering is calculated only when exporting the image.
        """
        self.histogram.setVisible(self.hist_check.isChecked())
        if self.source is None:
            self._refresh_timer.stop()
            self.preview_stack.setCurrentIndex(0)
            return
        self._refresh_timer.start()

    def _render_preview(self):
        if self.source is None:
            return
        try:
            # Fast preview: render target geometry and tonal adjustments, but use
            # no error diffusion. The selected dither is applied at export time.
            img = render_image(self.source, self.settings(), preview=True)
            qimg = ImageQt(img.convert("RGB")); pix = QPixmap.fromImage(qimg)
            self.preview_stack.setCurrentWidget(self.preview)
            self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
            w, h = img.size
            estimate = self.estimate_export_size(w, h)
            self.statusBar().showMessage(f"{w} × {h} px · {self.combo_value(self.output_mode)} · {self.combo_value(self.dither)} · {self.tr_text('Примерный размер файла')}: {estimate} · {self.tr_text('Предпросмотр; дизеринг применяется при экспорте')} · {self.source_path or ''}")
            if self.hist_check.isChecked():
                # Histogram must reflect tonal adjustments, before output-level
                # quantization, palette mapping, or dithering.
                histogram_img = render_image(self.source, self.settings(), preview=True, pre_quantization=True)
                self.draw_histogram(histogram_img)
            self.last_render = None  # never reuse a low-quality preview for final export
        except Exception as e:
            self.statusBar().showMessage(self.tr_text("Ошибка обработки: ") + str(e))

    def draw_histogram(self, img):
        """Draw a 256-bin luminance histogram, counting one value per pixel.

        Converting to L before counting avoids treating the R, G and B channels
        as three independent pixels, which distorted the previous histogram.
        """
        import numpy as np
        from PySide6.QtGui import QPainter, QPen, QColor

        width, height = 700, 90
        left, right, baseline = 8, width - 8, height - 13
        plot_width, plot_height = right - left, height - 25
        counts, bar_heights = histogram_data(img, plot_height)
        q = QImage(width, height, QImage.Format.Format_ARGB32)
        q.fill(0xFF202630)
        painter = QPainter(q)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(QPen(QColor(0xFF596273), 1))
        painter.drawLine(left, baseline, right, baseline)
        painter.setPen(QPen(QColor(0xFFE6EDF3), 1))
        for value, bar_height in enumerate(bar_heights):
            if bar_height <= 0:
                continue
            x = left + round(value * (plot_width - 1) / 255)
            painter.drawLine(x, baseline, x, baseline - int(bar_height))
        painter.setPen(QPen(QColor(0xFFB8C1CC), 1))
        painter.drawText(1, height - 1, "0")
        painter.drawText(width - 28, height - 1, "255")
        painter.end()
        self.histogram.setPixmap(QPixmap.fromImage(q).scaled(
            self.histogram.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self,event): super().resizeEvent(event); self.refresh()
    def set_crop_mode(self, enabled):
        self.crop_mode_enabled = bool(enabled)
        self.preview.setCursor(Qt.CursorShape.OpenHandCursor if enabled else Qt.CursorShape.ArrowCursor)
    def mouse_down(self,event):
        if self.crop_mode_enabled and self.source is not None:
            self.drag_pos=event.position(); self.preview.setCursor(Qt.CursorShape.ClosedHandCursor)
    def mouse_up(self,event):
        self.drag_pos=None
        self.preview.setCursor(Qt.CursorShape.OpenHandCursor if self.crop_mode_enabled else Qt.CursorShape.ArrowCursor)
    def mouse_move(self,event):
        if not self.crop_mode_enabled or self.drag_pos is None or self.source is None: return
        w,h=self.current_size(); scale=min(self.preview.width()/w,self.preview.height()/h)
        delta=event.position()-self.drag_pos; self.offset_x+=delta.x()/max(.01,scale); self.offset_y+=delta.y()/max(.01,scale); self.drag_pos=event.position(); self.refresh()
    def wheel(self,event):
        s=self.sliders["zoom"]; s.setValue(max(s.minimum(),min(s.maximum(),s.value()+(10 if event.angleDelta().y()>0 else -10))))
    @staticmethod
    def _save_indexed_bmp(image: Image.Image, path: str, colors: list[tuple[int, int, int]], color_distance: bool = False) -> None:
        from .formats import save_indexed_bmp
        save_indexed_bmp(image, path, colors, color_distance=color_distance)

    @staticmethod
    def _save_pxc(image: Image.Image, path: str, dither: str) -> None:
        from .formats import save_pxc
        save_pxc(image, path, dither)

    def export_one(self,fmt):
        if self.source is None: QMessageBox.information(self,self.tr_text("Export"),self.tr_text("Open an image first.")); return
        ext=fmt.lower(); default=Path(self.source_path or "wallpaper").stem+f".{ext}"
        filters={"BMP":"BMP image (*.bmp)","PNG":"PNG image (*.png)","PXC":"CrossPoint PXC (*.pxc)"}
        path,_=QFileDialog.getSaveFileName(self,self.tr_text("Export image"),default,filters[fmt])
        if not path:return
        if not Path(path).suffix: path += f".{ext}"
        try:
            img=render_image(self.source,self.settings(), preview=False)
            if fmt == "PXC":
                self._save_pxc(img, path, self.combo_value(self.dither))
            elif fmt == "PNG":
                from .formats import save_png_for_mode
                save_png_for_mode(img, path, self.combo_value(self.output_mode))
            else:
                mode=self.combo_value(self.output_mode)
                if mode == "4 gray levels":
                    self._save_indexed_bmp(img, path, [(0,0,0),(85,85,85),(170,170,170),(255,255,255)])
                elif mode == "16 gray levels":
                    self._save_indexed_bmp(img, path, [(v,v,v) for v in range(0,256,17)])
                elif mode == "256 gray levels (8-bit PNG)":
                    self._save_indexed_bmp(img, path, [(v,v,v) for v in range(256)])
                elif mode == "Spectra 6 palette":
                    self._save_indexed_bmp(img, path, [(0,0,0),(255,255,255),(220,0,0),(255,230,0),(0,80,200),(0,150,70)], color_distance=True)
                else:
                    img.convert("RGB").save(path,format="BMP")
            self.statusBar().showMessage(self.tr_text("Saved: ") + path)
        except Exception as e: QMessageBox.critical(self,self.tr_text("Export error"),str(e))
    def project_data(self):
        d=self.settings(); d["size"]=list(d["size"]); d.update({"version":2,"device":self.combo_value(self.device),"orientation":self.combo_value(self.orientation),"source_path":self.source_path,"preset":self.combo_value(self.preset)}); return d
    def save_project(self):
        path,_=QFileDialog.getSaveFileName(self,self.tr_text("Сохранить проект"),"wallpaper.xtws","EInkXT Wallpaper Studio project (*.xtws *.json)")
        if path:
            try: Path(path).write_text(json.dumps(self.project_data(),ensure_ascii=False,indent=2),encoding="utf-8")
            except Exception as e: QMessageBox.critical(self,self.tr_text("Ошибка проекта"),str(e))
    def load_project(self):
        path,_=QFileDialog.getOpenFileName(self,self.tr_text("Загрузить проект"),"","EInkXT Wallpaper Studio project (*.xtws *.json)")
        if not path:return
        try:
            d=json.loads(Path(path).read_text(encoding="utf-8")); self.set_combo_value(self.device, d.get("device","Custom")); self.set_combo_value(self.orientation, d.get("orientation","Портрет")); size=d.get("size",[528,792]); self.custom_w.setValue(int(size[0])); self.custom_h.setValue(int(size[1])); self.set_combo_value(self.fit, d.get("fit_mode","Cover")); self.rotation=int(d.get("rotation",0)); self.offset_x=float(d.get("offset_x",0)); self.offset_y=float(d.get("offset_y",0)); self.set_combo_value(self.dither, d.get("dither","Atkinson")); self.set_combo_value(self.output_mode, d.get("output_mode", "4 gray levels")); self.set_combo_value(self.preset, d.get("preset","Пользовательский"))
            for k,s in self.sliders.items():
                if k in d:s.setValue(int(d[k]))
            src=d.get("source_path")
            if src and Path(src).is_file(): self.load_image(src)
            self.refresh()
        except Exception as e: QMessageBox.critical(self,self.tr_text("Ошибка проекта"),str(e))
    def batch_export(self):
        files,_=QFileDialog.getOpenFileNames(self,self.tr_text("Выберите изображения для пакетной обработки"),"",IMAGE_FILTER)
        if not files:return
        folder=QFileDialog.getExistingDirectory(self,self.tr_text("Папка для результатов"))
        if not folder:return
        fmt,ok=QInputDialog.getItem(self,self.tr_text("Export format"),self.tr_text("Format"),["PNG","BMP","PXC"],0,False)
        if not ok:return
        settings=self.settings(); progress=QProgressDialog(self.tr_text("Обработка изображений…"),self.tr_text("Отмена"),0,len(files),self); progress.setWindowModality(Qt.WindowModality.WindowModal); done=0; errors=[]
        for i,path in enumerate(files):
            if progress.wasCanceled():break
            try:
                with Image.open(path) as im: result=render_image(im.convert("RGB"),settings)
                name=Path(path).stem+f"_wallpaper.{fmt.lower()}"; dest=Path(folder)/name
                if fmt=="PNG":
                    from .formats import save_png_for_mode
                    save_png_for_mode(result, str(dest), settings.get("output_mode", "4 gray levels"))
                elif fmt=="PXC": self._save_pxc(result, str(dest), settings.get("dither", "Atkinson"))
                elif settings.get("output_mode") == "4 gray levels": self._save_indexed_bmp(result, str(dest), [(0,0,0),(85,85,85),(170,170,170),(255,255,255)])
                else: result.convert("RGB").save(dest,format="BMP")
                done+=1
            except Exception as e: errors.append(f"{Path(path).name}: {e}")
            progress.setValue(i+1); QApplication.processEvents()
        msg=f"Успешно обработано: {done} из {len(files)}.\nПапка: {folder}"
        if errors: msg+="\n\nОшибки:\n"+"\n".join(errors[:10])
        QMessageBox.information(self,self.tr_text("Пакетная обработка"),msg)
    def dragEnterEvent(self,event):
        # Drag-and-drop is only an initial empty-state affordance. Once a source is
        # loaded, replacement is done explicitly through File > Open.
        if self.source is None and event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()
    def dropEvent(self,event):
        if self.source is not None: return
        urls=event.mimeData().urls()
        if urls: self.load_image(urls[0].toLocalFile())

def main():
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setWindowIcon(QIcon(str(resource_path("assets/EInkXTWallpaperStudio-app.ico")))); window=MainWindow(); window.showMaximized(); sys.exit(app.exec())
if __name__=="__main__": main()
