import aiohttp, aiofiles, asyncio, sys, json, os, shutil, time
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
    QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, QPoint, QByteArray, QRect, QSize, QPointF
from PySide6.QtGui import QColor, QMouseEvent, QFont, QPixmap, QIcon
from qasync import QEventLoop
from collections.abc import MutableMapping
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

class Components:
    def __init__(self):
        self._order = []
        self._widgets = {}

    def __setattr__(self, name, value):
        if isinstance(value, QWidget):  # only auto-register widgets
            self._order.append(name)
            self._widgets[name] = value
        super().__setattr__(name, value)

    def iter_widgets(self):
        for name in self._order:
            yield self._widgets[name]



class Pages:
    class Home(Page):
        def _init_widgets(self):
            # unimportant
            self.components = Components()

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            container = QWidget()
            container.setObjectName("scroll_content")
            scroll.setWidget(container)

            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            # layout.setSpacing(0)
            layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

            button_size = (250, 40)
            input_size = (400, 30)
            alignment = Qt.AlignmentFlag.AlignHCenter

            # do important stuff under here
            self.components.heading = QLabel("stupid stuff")

            self.components.input = QLineEdit("Type something here")
            self.components.input.setMinimumSize(*input_size)
            # self.components.input.setMaximumSize(*input_size)

            self.components.button = QPushButton("Run Async Task", flat=True)
            self.components.button.setMinimumSize(*button_size)
            # self.components.button.setMaximumSize(*button_size)
            self.components.button.clicked.connect(lambda: asyncio.create_task(self.do_async_button()))

            for i in range(2):
                setattr(self.components, f"what{i+1}", QLabel(f"stupid: {i+1}"))

            # finalize
            for widget in self.components.iter_widgets():
                layout.addWidget(widget, alignment=alignment)

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)

        async def do_async_button(self):
            print("Async button clicked!")
            self.components.async_btn.setEnabled(False)
            await asyncio.sleep(3)
            self.components.async_btn.setEnabled(True)
            print("Button ready again!")

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

        # Drag / resize flags
        self._dragging = False
        self._resizing = False
        self._drag_start_pos = QPoint()
        self._resize_direction = None
        self._resize_fixed = False
        self._resize_start_rect = None
        self._resize_edges = {}
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
        
        style += f"""
            /* General widgets */
            QWidget {{
                color: white;
            }}
            /* Text input fields */
            QLineEdit {{
                background-color: rgba(40, 40, 40, 0.9);
                color: white;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_THEME};
            }}
            QPushButton {{
                background-color: rgba(60, 60, 60, 0.9);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(80, 80, 80, 0.9);
            }}
            QPushButton:disabled {{
                background-color: rgba(60, 60, 60, 0.4);
                color: gray;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget {{
                background: transparent;
            }}
            QWidget#scroll_content {{
                background: transparent;
            }}
        """
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

    # --- Events ---
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
            return 'top-left'
        if top and right:
            return 'top-right'
        if bottom and left:
            return 'bottom-left'
        if bottom and right:
            return 'bottom-right'
        if left:
            return 'left'
        if right:
            return 'right'
        if top:
            return 'top'
        if bottom:
            return 'bottom'
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            global_pos = event.globalPosition().toPoint()

            if self.isMaximized():
                if self.title_bar.rect().contains(self.title_bar.mapFromGlobal(global_pos)):
                    self._dragging = True
                    self._drag_start_pos = global_pos
                    return

            if not self.isMaximized():
                self._resize_direction = self.get_resize_direction(pos)
                if self._resize_direction:
                    self._resizing = True
                    self._drag_start_pos = global_pos
                    self._resize_start_rect = self.geometry()
                    event.accept()
                    return
                
            if self.title_bar.rect().contains(self.title_bar.mapFromGlobal(global_pos)):
                self._dragging = True
                self._drag_start_pos = global_pos - self.frameGeometry().topLeft()
                event.accept()
                return

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event: QMouseEvent):
        global_pos = event.globalPosition().toPoint()

        if self._dragging:
            if self.isMaximized():
                # Calculate the offset where the cursor grabbed the title bar
                cursor_ratio_x = self._drag_start_pos.x() / self.width()
                cursor_ratio_y = self._drag_start_pos.y() / self.height()

                # Restore window
                self.showNormal()
                self.apply_style()

                # Move the window so the cursor stays at the same relative position
                new_x = global_pos.x() - int(cursor_ratio_x * self.width())
                new_y = global_pos.y() - int(cursor_ratio_y * self.height())
                self.move(new_x, new_y)

                # Update drag start pos to maintain smooth dragging
                self._drag_start_pos = QPoint(int(cursor_ratio_x * self.width()),
                                              int(cursor_ratio_y * self.height()))
            else:
                new_pos = global_pos - self._drag_start_pos
                self.move(new_pos)
            event.accept()
            return

        if self._resizing and self._resize_start_rect:
            # Resize disabled while maximized
            if not self.isMaximized():
                delta = global_pos - self._drag_start_pos
                rect = QRect(self._resize_start_rect)
                min_w, min_h = self.minimumWidth(), self.minimumHeight()

                if 'left' in self._resize_direction:
                    rect.setLeft(min(rect.right() - min_w, rect.left() + delta.x()))
                if 'right' in self._resize_direction:
                    rect.setRight(max(rect.left() + min_w, rect.right() + delta.x()))
                if 'top' in self._resize_direction:
                    rect.setTop(min(rect.bottom() - min_h, rect.top() + delta.y()))
                if 'bottom' in self._resize_direction:
                    rect.setBottom(max(rect.top() + min_h, rect.bottom() + delta.y()))

                self.setGeometry(rect)
                event.accept()
                return

        # Update cursor
        cursor = Qt.ArrowCursor
        if not self.isMaximized():
            direction = self.get_resize_direction(event.position().toPoint())
            if direction in ['left', 'right']:
                cursor = Qt.SizeHorCursor
            elif direction in ['top', 'bottom']:
                cursor = Qt.SizeVerCursor
            elif direction in ['top-left', 'bottom-right']:
                cursor = Qt.SizeFDiagCursor
            elif direction in ['top-right', 'bottom-left']:
                cursor = Qt.SizeBDiagCursor
        self.setCursor(cursor)
        super().mouseMoveEvent(event)



    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self._dragging:
                # Snap to top to maximize if released at top
                if not self.isMaximized():
                    cursor_y = event.globalPosition().y()
                    if cursor_y <= 0:
                        self._normal_geometry = self.geometry()
                        self.showMaximized()
                        self.apply_style()

            self._dragging = False
            self._resizing = False
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
class AsyncSynchronizedDict(MutableMapping):
    def __init__(self, filename):
        self.filename = filename
        self.data = {}

    # --- Dict-like behavior ---
    def __getitem__(self, key):
        return self.data[key]

    async def __setitem__(self, key, value):
        self.data[key] = value
        await self._write_to_file()

    async def __delitem__(self, key):
        del self.data[key]
        await self._write_to_file()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __contains__(self, key):
        return key in self.data

    # --- Dict methods pass-through ---
    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def as_dict(self):
        """Return the underlying dict."""
        return self.data

    # --- Load / Save ---
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

    async def update(self, other=None, **kwargs):
        """Update the dict and save asynchronously."""
        if other is None:
            other = {}
        elif isinstance(other, AsyncSynchronizedDict):
            other = other.data
        elif not isinstance(other, dict):
            raise TypeError("update() expects a dict or AsyncSynchronizedDict")
        self.data.update(other, **kwargs)
        await self._write_to_file()

    def __repr__(self):
        return f"AsyncSynchronizedDict({self.data})"


# -------------------- Merge Function --------------------
def merge_config(default: dict, current: dict) -> dict:
    """Recursively merge default into current, adding only missing keys."""
    for key, value in default.items():
        if key not in current:
            current[key] = value
        elif isinstance(value, dict) and isinstance(current.get(key), dict):
            merge_config(value, current[key])
    return current


# -------------------- Main Async --------------------
async def main_async(window):
    async with aiohttp.ClientSession() as session:
        CONFIG = AsyncSynchronizedDict(CONFIG_PATH)
        await CONFIG.load()
        current_config = CONFIG.as_dict()  # get the full dict

        try:
            async with session.get(f"https://rawcdn.githack.com/Inkthirsty/Inbox-Nuke/refs/heads/main/src/config.example.json?min=1") as response:
                response.raise_for_status()
                default_config = json.loads(await response.text())
                print("Default config:", json.dumps(default_config, indent=1))

                # Merge example/default config into current config, always
                merged = merge_config(default_config, current_config)

                # Save merged config back to file
                await CONFIG.update(merged)
                print("Config merged and saved successfully.")

        except aiohttp.ClientError as e:
            print(f"Error fetching remote config: {e}")

    # Trigger the window's async task
    asyncio.create_task(window.do_async_task())
    await asyncio.sleep(0)

# -------------------- Entry Point --------------------
def main():
    try:
        app = QApplication(sys.argv)
        # The main stylesheet is now applied in the MainWindow class
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
