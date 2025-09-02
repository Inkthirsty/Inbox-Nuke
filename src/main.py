import aiohttp, asyncio, sys, json, os, shutil
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QStackedWidget, QPushButton, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout
)
from PySide6.QtCore import Qt, QPoint, QByteArray, QRect, QSize
from PySide6.QtGui import QColor, QMouseEvent, QFont, QPixmap, QIcon
from qasync import QEventLoop

DIRECTORY = os.path.dirname(__file__)

CONFIG_FILENAME = "config.json"
CONFIG_PATH = os.path.join(DIRECTORY, CONFIG_FILENAME)

TEMP_FOLDER = os.path.join(DIRECTORY, "temp")
if os.path.exists(TEMP_FOLDER):
    shutil.rmtree(TEMP_FOLDER)
os.makedirs(TEMP_FOLDER, exist_ok=True)

COLOR_BACKGROUND = "#1c1c1c"
COLOR_FOREGROUND = "#162034"
COLOR_THEME = "#385389"

TITLE = "Inbox Nuke"
VERSION = "1.0.0"

class Page(QWidget):
    def __init__(self):
        super().__init__()
        self._init_widgets()

    def _init_widgets(self):
        pass

    def reset(self):
        for i in reversed(range(self.layout().count() if self.layout() else 0)):
            item = self.layout().takeAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        self._init_widgets()

class Pages:
    class Home(Page):
        def _init_widgets(self):
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(QLabel("homer"), alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

            def test():
                print(self.input.text())

            self.input = QLineEdit("Type something here")
            layout.addWidget(self.input)

    class Emails(Page):
        def _init_widgets(self):
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(QLabel("homer"), alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.input = QLineEdit("Type something here")
            layout.addWidget(self.input)
    
    class Settings(Page):
        def _init_widgets(self):
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(QLabel("homer"), alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.input = QLineEdit("Type something here")
            layout.addWidget(self.input)

    @classmethod
    def instigate(cls):
        for name, page_cls in vars(cls).items():
            if isinstance(page_cls, type) and issubclass(page_cls, Page):
                setattr(cls, name, page_cls())

class MainWindow(QWidget):
    RESIZE_MARGIN = 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.setMinimumSize(740, 460)
        self.resize(740, 460)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        font = QFont("Consolas", 12)
        font.setBold(True)
        self.setFont(font)

        self._normal_style = f"""
            QFrame#container {{
                background-color: {COLOR_BACKGROUND};
                border: 3px solid {COLOR_THEME};
                border-radius: 12px;
            }}
            QFrame#titlebar {{
                background-color: {COLOR_THEME};
            }}
            QStackedWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:2,
                    stop:0 {COLOR_BACKGROUND},
                    stop:1 {COLOR_FOREGROUND}
                );
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """

        self._maximized_style = f"""
            QFrame#container {{
                background-color: {COLOR_BACKGROUND};
                border: none;
                border-radius: 0px;
            }}
            QFrame#titlebar {{
                background-color: {COLOR_THEME};
            }}
            QStackedWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:2,
                    stop:0 {COLOR_BACKGROUND},
                    stop:1 {COLOR_FOREGROUND}
                );
                border-radius: 0px;
            }}
        """

        container = QFrame(self)
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(COLOR_THEME))
        glow.setBlurRadius(40)
        glow.setOffset(0)
        container.setGraphicsEffect(glow)

        title_bar = QFrame()
        title_bar.setObjectName("titlebar")
        title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        self.title_label = QLabel(f"{TITLE} v{VERSION}")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.btn_min = QPushButton()
        self.btn_max = QPushButton()
        self.btn_close = QPushButton()
        icon_size = QSize(int(0.4 * 40), int(0.4 * 30))
        self.btn_min.setIcon(QIcon("assets/minus.png"))
        self.btn_min.setIconSize(icon_size)
        self.btn_max.setIcon(QIcon("assets/square1.png"))
        self.btn_max.setIconSize(icon_size)
        self.btn_close.setIcon(QIcon("assets/cross.png"))
        self.btn_close.setIconSize(icon_size)
        for button in (self.btn_min, self.btn_max, self.btn_close):
            button.setFixedSize(40, 30)
            button.setFont(font)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.2);
                    border-radius: 12px;
                }
            """)
        title_layout.addWidget(self.btn_min, alignment=Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.btn_max, alignment=Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        container_layout.addWidget(title_bar)
        container_layout.addWidget(self.stack)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.pages = {}
        for name, obj in vars(Pages).items():
            if isinstance(obj, Page):
                self.pages[name] = obj
                self.stack.addWidget(obj)
        self.switchPage(Pages.Home)

        self.dragging = False
        self.drag_pos = QPoint()
        self._resizing = False
        self._resize_dir = None
        self._maximized = False
        self._normal_geometry = self.geometry()
        self._drag_ratio_x = 0
        self._drag_ratio_y = 0
        self._dragged_to_top = False

        self.btn_close.clicked.connect(lambda: self.close())
        self.btn_min.clicked.connect(lambda: self.showMinimized())
        self.btn_max.clicked.connect(lambda: self.toggleMaximizeRestore())

        self.setMouseTracking(True)
        self._enable_mouse_tracking(self)
        self.setStyleSheet(self._normal_style)

    def _enable_mouse_tracking(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)

    def toggleMaximizeRestore(self):
        if self._maximized:
            self.setGeometry(self._normal_geometry)
            self.btn_max.setIcon(QIcon("assets/square1.png"))
            self.setStyleSheet(self._normal_style)
            self._maximized = False
        else:
            self._normal_geometry = self.geometry()
            self.setGeometry(QApplication.primaryScreen().availableGeometry())
            self.btn_max.setIcon(QIcon("assets/square2.png"))
            self.setStyleSheet(self._maximized_style)
            self._maximized = True

    def resizeEvent(self, event):
        if not self._maximized:
            self._normal_geometry = self.geometry()
        super().resizeEvent(event)

    def moveEvent(self, event):
        if not self._maximized:
            self._normal_geometry = self.geometry()
        super().moveEvent(event)


    def getPage(self) -> Page:
        return self.stack.currentWidget()

    def switchPage(self, page: Page):
        if not self.getPage() != page:
            self.stack.setCurrentWidget(page)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position().toPoint()
        rect = self.rect()
        margin = self.RESIZE_MARGIN

        if self._maximized:
            self.dragging = True
            self._drag_ratio_x = pos.x() / self.width()
            self._drag_ratio_y = pos.y() / self.height()
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            return

        if pos.x() < margin and pos.y() < margin:
            self._resize_dir = "topleft"
        elif pos.x() > rect.width() - margin and pos.y() < margin:
            self._resize_dir = "topright"
        elif pos.x() < margin and pos.y() > rect.height() - margin:
            self._resize_dir = "bottomleft"
        elif pos.x() > rect.width() - margin and pos.y() > rect.height() - margin:
            self._resize_dir = "bottomright"
        elif pos.x() < margin:
            self._resize_dir = "left"
        elif pos.x() > rect.width() - margin:
            self._resize_dir = "right"
        elif pos.y() < margin:
            self._resize_dir = "top"
        elif pos.y() > rect.height() - margin:
            self._resize_dir = "bottom"
        else:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            return

        self._resizing = True
        self._start_geom = self.geometry()
        self._start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        rect = self.rect()
        margin = self.RESIZE_MARGIN

        if not self._resizing and not self.dragging and not self._maximized:
            if pos.x() < margin and pos.y() < margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif pos.x() > rect.width() - margin and pos.y() < margin:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif pos.x() < margin and pos.y() > rect.height() - margin:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif pos.x() > rect.width() - margin and pos.y() > rect.height() - margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif pos.x() < margin or pos.x() > rect.width() - margin:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif pos.y() < margin or pos.y() > rect.height() - margin:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.dragging:
            if self._maximized:
                cursor = event.globalPosition().toPoint()
                geom = QRect(self._normal_geometry)
                new_x = int(cursor.x() - self._drag_ratio_x * geom.width())
                new_y = int(cursor.y() - self._drag_ratio_y * geom.height())
                self.setGeometry(geom)
                self.move(new_x, new_y)
                self._maximized = False
                self.btn_max.setIcon(QIcon("assets/square1.png"))
                self.setStyleSheet(self._normal_style)
            else:
                self.move(event.globalPosition().toPoint() - self.drag_pos)
                self._dragged_to_top = event.globalPosition().y() <= 0

        elif self._resizing and not self._maximized:
            delta = event.globalPosition().toPoint() - self._start_pos
            geom = QRect(self._start_geom)
            if "left" in self._resize_dir:
                new_left = geom.left() + delta.x()
                if geom.right() - new_left < self.minimumWidth():
                    new_left = geom.right() - self.minimumWidth()
                geom.setLeft(new_left)
            if "right" in self._resize_dir:
                new_right = geom.right() + delta.x()
                if new_right - geom.left() < self.minimumWidth():
                    new_right = geom.left() + self.minimumWidth()
                geom.setRight(new_right)
            if "top" in self._resize_dir:
                new_top = geom.top() + delta.y()
                if geom.bottom() - new_top < self.minimumHeight():
                    new_top = geom.bottom() - self.minimumHeight()
                geom.setTop(new_top)
            if "bottom" in self._resize_dir:
                new_bottom = geom.bottom() + delta.y()
                if new_bottom - geom.top() < self.minimumHeight():
                    new_bottom = geom.top() + self.minimumHeight()
                geom.setBottom(new_bottom)
            self.setGeometry(geom)


    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragged_to_top and not self._maximized:
            self._normal_geometry = self.geometry()
            self.setGeometry(QApplication.primaryScreen().availableGeometry())
            self._maximized = True
            self.btn_max.setIcon(QIcon("assets/square2.png"))
            self.setStyleSheet(self._maximized_style)

        self.dragging = False
        self._resizing = False
        self._resize_dir = None
        self._dragged_to_top = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    async def do_async_task(self):
        return
        while True:
            await asyncio.sleep(1)



async def main_async(window):
    asyncio.create_task(window.do_async_task())
    await asyncio.sleep(0)

def main():
    try:
        app = QApplication(sys.argv)
        Pages.instigate()
        window = MainWindow()
        window.show()

        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        with loop:
            loop.create_task(main_async(window))
            loop.run_forever()
    finally:
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)

if __name__ == "__main__":
    main()
