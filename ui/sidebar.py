import os

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QApplication,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap

from core import i18n

_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons")
_cache = {}
_current_text_color = "#ffffff"


def set_icon_theme_color(text_color):
    """Set the color to use for bundled SVG icons."""
    global _current_text_color
    _current_text_color = text_color
    _cache.clear()


def get_icon(name, size=16):
    """Get icon from bundled SVGs with theme-aware coloring."""
    bundled = os.path.join(_ICONS_DIR, f"{name}.svg")
    if not os.path.exists(bundled):
        return QIcon()

    color = _current_text_color
    cache_key = (name, color, size)
    if cache_key in _cache:
        return _cache[cache_key]

    with open(bundled, "r") as f:
        svg_data = f.read()

    svg_data = svg_data.replace("currentColor", color)

    pixmap = QPixmap()
    pixmap.loadFromData(svg_data.encode("utf-8"), "SVG")

    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    icon = QIcon(scaled)
    _cache[cache_key] = icon
    return icon


def invalidate_icon_cache():
    """Clear cached icons when theme changes."""
    _cache.clear()


class Sidebar(QWidget):
    pageChanged = Signal(str)
    fullscreenRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)

        self.nav_buttons = {}
        # Keep a mapping of nav item name -> icon name to allow icon refreshes when theme changes
        self.nav_icon_names = {}
        self.add_nav_item("library", i18n.t("library"), "view-grid")
        self.add_nav_item("monitors", i18n.t("monitors"), "video-display")
        self.add_nav_item("diagnostics", i18n.t("diagnostics"), "utilities-system-monitor")
        self.add_nav_item("settings", i18n.t("settings"), "emblem-system")
        self.add_nav_item("about", i18n.t("about"), "help-about")

        layout.addStretch()

        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setObjectName("fullscreen_btn")
        self.fullscreen_btn.setCursor(Qt.PointingHandCursor)
        self.fullscreen_btn.setIcon(get_icon("view-fullscreen", 18))
        self.fullscreen_btn.setToolTip(i18n.t("fullscreen_tooltip"))
        self.fullscreen_btn.clicked.connect(self.fullscreenRequested.emit)
        layout.addWidget(self.fullscreen_btn)

        self.version = QLabel(i18n.t("version") + " v1.5 Beta")
        self.version.setStyleSheet(
            "color: #666; font-size: 10px; margin-right: 10px; border: none;"
        )
        self.version.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version)

        self.set_active("library")

    def add_nav_item(self, name, label, icon_name):
        btn = QPushButton(f" {label}")
        btn.setObjectName("nav_btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(get_icon(icon_name, 16))

        btn.clicked.connect(lambda: self.on_btn_clicked(name))
        self.nav_buttons[name] = btn
        # store icon name for future refreshes
        self.nav_icon_names[name] = icon_name
        self.layout().addWidget(btn)

    def on_btn_clicked(self, name):
        self.set_active(name)
        self.pageChanged.emit(name)

    def set_active(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.setProperty("active", btn_name == name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh_icons(self):
        """Reapply icons with current theme colors."""
        invalidate_icon_cache()
        for name, btn in self.nav_buttons.items():
            icon_name = self.nav_icon_names.get(name)
            if icon_name and btn:
                btn.setIcon(get_icon(icon_name, 16))

        self.fullscreen_btn.setIcon(get_icon("view-fullscreen", 18))
