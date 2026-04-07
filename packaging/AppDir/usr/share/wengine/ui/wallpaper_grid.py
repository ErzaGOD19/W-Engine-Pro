from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QListView


class WallpaperGrid(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWordWrap(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setIconSize(QSize(200, 150))
        self.setGridSize(QSize(220, 200))
        self.setUniformItemSizes(True)
        self.setSpacing(10)

        # Performance optimization: Disable updates during bulk loads
        self.setUpdatesEnabled(True)

        self.model = QStandardItemModel()
        self.setModel(self.model)

    def add_wallpaper(self, name, type_label, thumbnail_path=None, data=None):
        item = QStandardItem(name)

        if thumbnail_path:
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                # Only scale if needed and use FastTransformation if possible for speed,
                # but SmoothTransformation is better for thumbnails.
                # However, we can check size first.
                if pixmap.width() > 250 or pixmap.height() > 200:
                    pixmap = pixmap.scaled(
                        200, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                    )
                item.setIcon(QIcon(pixmap))
            else:
                self._set_placeholder(item)
        else:
            self._set_placeholder(item)

        item.setToolTip(f"{name}\nType: {type_label}")
        item.setData(type_label, Qt.UserRole + 1)
        item.setData(data, Qt.UserRole + 2)

        self.model.appendRow(item)

    def _set_placeholder(self, item):
        # Cache placeholder pixmap to avoid recreating it
        if not hasattr(self, "_placeholder_pixmap"):
            self._placeholder_pixmap = QPixmap(200, 150)
            self._placeholder_pixmap.fill(QColor("#333333"))
        item.setIcon(QIcon(self._placeholder_pixmap))

    def select_wallpaper(self, identifier=None):
        """
        Select a wallpaper by name or by stored data (path/url).
        identifier: matching item.text() or item.data(Qt.UserRole + 2)
        """
        from PySide6.QtCore import QItemSelectionModel

        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if not item:
                continue
            item_data = item.data(Qt.UserRole + 2)
            if (
                identifier is None
                or identifier == item.text()
                or identifier == item_data
            ):
                index = self.model.index(row, 0)
                # Clear previous selection and select this item
                self.selectionModel().clearSelection()
                self.selectionModel().select(
                    index, QItemSelectionModel.Select | QItemSelectionModel.Rows
                )
                self.setCurrentIndex(index)
                self.scrollTo(index)
                return True
        return False

    def update_thumbnail(self, identifier, thumbnail_path):
        """
        Update thumbnail for an existing wallpaper item.
        identifier: matching item.data(Qt.UserRole + 2) (URL or path)
        """
        from PySide6.QtGui import QIcon, QPixmap

        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if not item:
                continue
            item_data = item.data(Qt.UserRole + 2)
            if item_data == identifier:
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    if pixmap.width() > 250 or pixmap.height() > 200:
                        pixmap = pixmap.scaled(
                            200,
                            150,
                            Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation,
                        )
                    item.setIcon(QIcon(pixmap))
                return True
        return False

    def clear(self):
        self.model.clear()
