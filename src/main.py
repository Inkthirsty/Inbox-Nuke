import aiohttp, aiofiles, asyncio, sys, json, os, shutil
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QPoint, QByteArray, QRect, QSize, QPointF
from PySide6.QtGui import QColor, QMouseEvent, QFont, QPixmap, QIcon
from qasync import QEventLoop
from endpoints import Endpoints

DIRECTORY = os.path.dirname(__file__)

CONFIG_FILENAME = "config.json"
CONFIG_PATH = os.path.join(DIRECTORY, CONFIG_FILENAME)

TEMP_PATH = os.path.join(DIRECTORY, "temp")
if os.path.exists(TEMP_PATH):
    shutil.rmtree(TEMP_PATH)
os.makedirs(TEMP_PATH, exist_ok=True)

COLOR_BACKGROUND = "#1c1c1c"
COLOR_FOREGROUND = "#162034"
COLOR_THEME = "#385389"

TITLE = "Inbox Nuke"
VERSION = "1.0.0"

# -------------------- Page Classes --------------------
class Page(QWidget):
    def __init__(self):
        super().__init__()
        self._init_widgets()

    def _init_widgets(self):
        pass

    async def on_show(self):
        """Override for async setup when shown"""
        pass

    async def on_hide(self):
        """Override for async cleanup when hidden"""
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
            layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            layout.addWidget(QLabel("Home Page"), alignment=Qt.AlignmentFlag.AlignHCenter)

            button_size = (200, 30)

            self.input = QLineEdit("Type something here")
            layout.addWidget(self.input,  alignment=Qt.AlignmentFlag.AlignHCenter)

            self.async_btn = QPushButton("Run Async Task", flat=True)
            self.async_btn.setMinimumSize(*button_size)
            self.async_btn.setMaximumSize(*button_size)
            layout.addWidget(self.async_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
            
            self.async_btn.clicked.connect(
                lambda: asyncio.create_task(self.do_async_button())
            )

        async def do_async_button(self):
            print("Async button clicked!")
            self.async_btn.setEnabled(False)
            await asyncio.sleep(3)
            self.async_btn.setEnabled(True)
            print("Button ready again!")

    class Emails(Page):
        def _init_widgets(self):
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Emails Page"))
            self.input = QLineEdit("Type something here")
            layout.addWidget(self.input)

    class Settings(Page):
        def _init_widgets(self):
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Settings Page"))
            self.input = QLineEdit("Type something here")
            layout.addWidget(self.input)

    @classmethod
    def instigate(cls):
        for name, page_cls in vars(cls).items():
            if isinstance(page_cls, type) and issubclass(page_cls, Page):
                setattr(cls, name, page_cls())

# -------------------- Main Window --------------------
class MainWindow(QWidget):
    RESIZE_MARGIN = 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{TITLE} (v{VERSION})")
        self.setMinimumSize(740, 460)
        self.resize(740, 460)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setWindowIcon(QIcon(os.path.join(DIRECTORY, "assets/icon.ico")))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._dragging = False
        self._resizing = False
        self._drag_start_pos = QPoint()
        self._resize_direction = None
        self._normal_geometry = self.geometry()
        self._setup_ui()
        self._setup_connections()
        self._setup_mouse_events()
        self.apply_style()

    # --- UI Setup ---
    def _setup_ui(self):
        self.container = QFrame(self)
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(COLOR_THEME))
        glow.setBlurRadius(40)
        glow.setOffset(0)
        self.container.setGraphicsEffect(glow)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("titlebar")
        self.title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        self.title_label = QLabel(f"{TITLE} (v{VERSION})")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.btn_min = QPushButton()
        self.btn_max = QPushButton()
        self.btn_close = QPushButton()
        button_size = QSize(40, 30)
        icon_size = QSize(int(0.4 * 40), int(0.4 * 30))
        self.btn_min.setIcon(QIcon(os.path.join(DIRECTORY, "assets/minus.png")))
        self.btn_min.setIconSize(icon_size)
        self.btn_max.setIcon(QIcon(os.path.join(DIRECTORY, "assets/square1.png")))
        self.btn_max.setIconSize(icon_size)
        self.btn_close.setIcon(QIcon(os.path.join(DIRECTORY, "assets/cross.png")))
        self.btn_close.setIconSize(icon_size)
        for button in (self.btn_min, self.btn_max, self.btn_close):
            button.setFixedSize(button_size)
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.2);
                    border-radius: 12px;
                }
            """
            )
        title_layout.addWidget(self.btn_min, alignment=Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.btn_max, alignment=Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        container_layout.addWidget(self.title_bar)
        container_layout.addWidget(self.stack)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        self.pages = {}
        for name, obj in vars(Pages).items():
            if isinstance(obj, Page):
                self.pages[name] = obj
                self.stack.addWidget(obj)

    # --- Connections ---
    def _setup_connections(self):
        self.btn_close.clicked.connect(self.close)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggleMaximizeRestore)

    def _setup_mouse_events(self):
        self.setMouseTracking(True)
        self.title_bar.setMouseTracking(True)
        for widget in self.findChildren(QWidget):
            widget.setMouseTracking(True)

    # --- Style ---
    def apply_style(self):
        if self.isMaximized():
            style = f"""
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
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {COLOR_BACKGROUND},
                        stop:0.6 {COLOR_FOREGROUND},
                        stop:1 {COLOR_FOREGROUND}
                    );
                    border-radius: 0px;
                }}
            """
            self.btn_max.setIcon(QIcon(os.path.join(DIRECTORY, "assets/square2.png")))
        else:
            style = f"""
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
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {COLOR_BACKGROUND},
                        stop:0.6 {COLOR_FOREGROUND},
                        stop:1 {COLOR_FOREGROUND}
                    );
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                }}
            """
            self.btn_max.setIcon(QIcon(os.path.join(DIRECTORY, "assets/square1.png")))
        self.setStyleSheet(style)

    def toggleMaximizeRestore(self):
        if self.isMaximized():
            self.showNormal()
            self.apply_style()
        else:
            self.showMaximized()
            self.apply_style()

    # --- Page Switching ---
    async def switchPage(self, page: Page):
        current = self.getPage()
        if current and hasattr(current, "on_hide"):
            await current.on_hide()
        if self.getPage() != page:
            self.stack.setCurrentWidget(page)
            if hasattr(page, "on_show"):
                await page.on_show()

    def getPage(self) -> Page:
        return self.stack.currentWidget()

    # --- Events (unchanged from your original) ---
    def resizeEvent(self, event):
        if not self.isMaximized():
            self._normal_geometry = self.geometry()
        super().resizeEvent(event)

    def moveEvent(self, event):
        if not self.isMaximized():
            self._normal_geometry = self.geometry()
        super().moveEvent(event)

    def get_resize_direction(self, pos: QPoint):
        rect = self.rect()
        left = pos.x() <= self.RESIZE_MARGIN
        right = pos.x() >= rect.width() - self.RESIZE_MARGIN
        top = pos.y() <= self.RESIZE_MARGIN
        bottom = pos.y() >= rect.height() - self.RESIZE_MARGIN

        if top and left:
            return Qt.CursorShape.SizeFDiagCursor  # top-left
        if top and right:
            return Qt.CursorShape.SizeBDiagCursor  # top-right
        if bottom and left:
            return Qt.CursorShape.SizeBDiagCursor  # bottom-left
        if bottom and right:
            return Qt.CursorShape.SizeFDiagCursor  # bottom-right
        if left:
            return Qt.CursorShape.SizeHorCursor
        if right:
            return Qt.CursorShape.SizeHorCursor
        if top:
            return Qt.CursorShape.SizeVerCursor
        if bottom:
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor


    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            global_pos = event.globalPosition().toPoint()
            local_pos = event.position().toPoint()
            if self.title_bar.rect().contains(self.title_bar.mapFromGlobal(global_pos)):
                self._dragging = True
                self._resizing = False
                if self.isMaximized():
                    self._drag_ratio_x = local_pos.x() / self.width()
                    self._drag_ratio_y = local_pos.y() / self.height()
                    self.showNormal()
                    self.apply_style()
                    new_x = int(global_pos.x() - self._drag_ratio_x * self.width())
                    new_y = int(global_pos.y() - self._drag_ratio_y * self.height())
                    self.move(new_x, new_y)
                    self._drag_start_pos = global_pos - QPoint(new_x, new_y)
                else:
                    self._drag_start_pos = global_pos - self.frameGeometry().topLeft()
                event.accept()
                return
            self._resize_direction = self.get_resize_direction(local_pos)
            if self._resize_direction != Qt.CursorShape.ArrowCursor:
                self._resizing = True
                self._dragging = False
                self._drag_start_pos = global_pos
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        global_pos = event.globalPosition().toPoint()

        if self._dragging:
            new_pos = global_pos - self._drag_start_pos
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            padding = 50
            new_x = max(-self.width() + padding, min(new_pos.x(), screen_geometry.width() - padding))
            new_y = max(0, min(new_pos.y(), screen_geometry.height() - padding))
            self.move(new_x, new_y)
            event.accept()
            return

        if self._resizing:
            diff = global_pos - self._drag_start_pos
            rect = self.geometry()

            if self._resize_direction == Qt.CursorShape.SizeHorCursor:
                if event.position().x() < rect.width() / 2:  # resizing from left
                    rect.setLeft(rect.left() + diff.x())
                else:  # resizing from right
                    rect.setRight(rect.right() + diff.x())
            elif self._resize_direction == Qt.CursorShape.SizeVerCursor:
                if event.position().y() < rect.height() / 2:  # resizing from top
                    rect.setTop(rect.top() + diff.y())
                else:  # resizing from bottom
                    rect.setBottom(rect.bottom() + diff.y())
            elif self._resize_direction == Qt.CursorShape.SizeFDiagCursor:
                rect.setLeft(rect.left() + diff.x())
                rect.setTop(rect.top() + diff.y())
            elif self._resize_direction == Qt.CursorShape.SizeBDiagCursor:
                rect.setRight(rect.right() + diff.x())
                rect.setBottom(rect.bottom() + diff.y())

            self.setGeometry(rect)
            self._drag_start_pos = global_pos
            event.accept()
            return

        if not self.isMaximized():
            self.setCursor(self.get_resize_direction(event.position().toPoint()))
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)



    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._resizing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            if self.y() <= 0 and event.globalPosition().y() <= 5:
                self._normal_geometry = self.geometry()
                self.showMaximized()
                self.apply_style()
            elif self.y() < 10:
                self.move(self.x(), 0)
            event.accept()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.title_bar.rect().contains(self.title_bar.mapFromGlobal(event.globalPosition().toPoint())):
                self.toggleMaximizeRestore()
            event.accept()
        super().mouseDoubleClickEvent(event)

    # --- Dummy Async Loop ---
    async def do_async_task(self):
        while True:
            await asyncio.sleep(1)

# -------------------- Async Config --------------------
class AsyncSynchronizedDict:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}

    async def load(self):
        try:
            if not os.path.exists(self.filename):
                raise FileNotFoundError
            async with aiofiles.open(self.filename, 'r') as f:
                content = await f.read()
                self.data = json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}

    async def _write_to_file(self):
        async with aiofiles.open(self.filename, 'w') as f:
            await f.write(json.dumps(self.data, indent=4))

    async def __setitem__(self, key, value):
        self.data[key] = value
        await self._write_to_file()

    async def __getitem__(self, key):
        return self.data[key]

    async def __delitem__(self, key):
        del self.data[key]
        await self._write_to_file()

    async def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)
        await self._write_to_file()
    
    def get(self):
        return self.data.get
    
    def __repr__(self):
        return f"AsyncSynchronizedDict({self.data})"

# -------------------- Main Async --------------------
async def main_async(window):
    async with aiohttp.ClientSession() as session:
        CONFIG = AsyncSynchronizedDict(CONFIG_PATH)
        await CONFIG.load()
        if not CONFIG.get():
            try:
                async with session.get("https://raw.githubusercontent.com/Inkthirsty/Inbox-Nuke/refs/heads/main/src/config.example.json") as response:
                    response.raise_for_status()
                    resp = json.loads(await response.text())

                    for key, value in resp.items():
                        if not CONFIG.get(key):
                            CONFIG
                    await CONFIG.update(resp)
                    print("config downloaded and saved")
            except aiohttp.ClientError as e:
                print(f"Error fetching remote config: {e}")

    asyncio.create_task(window.do_async_task())
    await asyncio.sleep(0)

# -------------------- Entry Point --------------------
def main():
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(os.path.join(DIRECTORY, "assets/icon.ico")))
        font = QFont("Consolas", 12)
        font.setBold(True)
        app.setFont(font)
        Pages.instigate()
        window = MainWindow()
        window.show()
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        with loop:
            loop.create_task(window.switchPage(Pages.Home))
            loop.create_task(main_async(window))
            loop.run_forever()
    finally:
        if os.path.exists(TEMP_PATH):
            shutil.rmtree(TEMP_PATH)

if __name__ == "__main__":
    main()
