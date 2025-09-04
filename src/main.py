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
    QScrollArea
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QFont, QIcon, QCursor
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

colors = ["#162034", "#06163B"]
COLOR_BACKGROUND = "#1c1c1c" # "#1c1c1c"
COLOR_FOREGROUND = "#162034" # "#162034"
COLOR_THEME = COLOR_FOREGROUND # "#3d3f4e" # "#386a8a"

TITLE = "Inbox Nuke"
VERSION = "1.0.0"

# -------------------- Page Classes --------------------
class Page(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window  # <--- store reference
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
            # config
            margins = (0, 0, 0, 0)
            button_size = (300, 40)
            input_size = (400, 30)

            # unimportant
            self.components = Components()

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setContentsMargins(*margins)
            scroll.setFrameShape(QScrollArea.NoFrame)
            container = QWidget()
            container.setContentsMargins(*margins)
            container.setObjectName("scroll_content")
            scroll.setWidget(container)

            layout = QVBoxLayout(container)
            layout.setContentsMargins(*margins)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # do important stuff under here
            self.components.heading = QLabel("what would you like to do today?")
            self.components.heading.setStyleSheet("""font-size: 20pt""")
            self.components.heading2 = QLabel("made by max")
            self.components.heading2.setStyleSheet("""padding-bottom: 20px;font-size: 10pt;font-weight: normal""")

            """
            self.components.input = QLineEdit("Type something here")
            self.components.input.setFixedSize(*input_size)
            """

            self.components.button = QPushButton("Nuke a random country", flat=True)
            self.components.button.setFixedSize(*button_size)
            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Other)))

            self.components.button2 = QPushButton("Kick a toddler", flat=True)
            self.components.button2.setFixedSize(*button_size)

            self.components.button3 = QPushButton("Do something illegal", flat=True)
            self.components.button3.setFixedSize(*button_size)

            custom_align = {}

            # finalize
            for widget in self.components.iter_widgets():
                layout.addWidget(widget, alignment=custom_align.get(widget, Qt.AlignmentFlag.AlignHCenter))

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)

        async def do_async_button(self):
            print("Async button clicked!")
            self.components.button.setEnabled(False)
            await asyncio.sleep(3)
            self.components.button.setEnabled(True)
            print("Button ready again!")


            
    class Other(Page):
        def _init_widgets(self):
            # config
            margins = (0, 0, 0, 0)
            button_size = (250, 40)
            input_size = (400, 30)

            # unimportant
            self.components = Components()

            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setContentsMargins(*margins)
            scroll.setFrameShape(QScrollArea.NoFrame)
            container = QWidget()
            container.setContentsMargins(*margins)
            container.setObjectName("scroll_content")
            scroll.setWidget(container)

            layout = QVBoxLayout(container)
            layout.setContentsMargins(*margins)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # do important stuff under here
            self.components.button = QPushButton("Back", flat=True)
            self.components.button.setFixedHeight(30)
            self.components.button.adjustSize()
            self.components.button.move(0, 0)
            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Home)))

            self.components.heading = QLabel("woah other page!")
            self.components.heading.setStyleSheet("""font-size: 20pt""")
            self.components.heading2 = QLabel("fuck you")
            self.components.heading2.setStyleSheet("""padding-bottom: 20px;font-size: 10pt;font-weight: normal""")

            custom_align = {
                self.components.button: Qt.AlignmentFlag.AlignLeft
            }

            # finalize
            for widget in self.components.iter_widgets():
                print("widget:", widget, custom_align.get(widget))
                layout.addWidget(widget, alignment=custom_align.get(widget, Qt.AlignmentFlag.AlignHCenter))

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)

    @classmethod
    def instigate(cls, window):
        for name, page_cls in vars(cls).items():
            if isinstance(page_cls, type) and issubclass(page_cls, Page) and page_cls is not Page:
                setattr(cls, name, page_cls(window))

# -------------------- Main Window --------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{TITLE} v{VERSION}")
        self.setMinimumSize(740, 460)
        self.resize(740, 460)
        self.setWindowFlags(Qt.WindowType.Window)  # normal OS window
        self.setWindowIcon(QIcon(os.path.join(DIRECTORY, "assets/icon.ico")))

        self._setup_ui()
        self.apply_style()

    # --- UI Setup ---
    def _setup_ui(self):
        # just the stack, no custom container/titlebar
        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)

        # add pages
        for obj in vars(Pages).values():
            if isinstance(obj, Page):
                self.stack.addWidget(obj)

    def apply_style(self):
        # simplified styling for normal window
        style = f"""
            QWidget {{
                color: white;
            }}
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
            QStackedWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0.5, y2:1,
                    stop:0 {COLOR_BACKGROUND},
                    stop:1 {COLOR_FOREGROUND}
                );
                border-radius: 0px;
            }}
        """
        self.setStyleSheet(style)

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

class AsyncSynchronizedDict(MutableMapping):
    def __init__(self, filename):
        self.filename = filename
        self.data = {}

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

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def as_dict(self):
        return self.data

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

def merge_config(default: dict, current: dict) -> dict:
    """Recursively merge default into current, adding only missing keys."""
    for key, value in default.items():
        if key not in current:
            current[key] = value
        elif isinstance(value, dict) and isinstance(current.get(key), dict):
            merge_config(value, current[key])
    return current

async def main_async(window):
    async with aiohttp.ClientSession() as session:
        CONFIG = AsyncSynchronizedDict(CONFIG_PATH)
        await CONFIG.load()
        current_config = CONFIG.as_dict()

        try:
            async with session.get(f"https://rawcdn.githack.com/Inkthirsty/Inbox-Nuke/refs/heads/main/src/config.example.json?min=1") as response:
                response.raise_for_status()
                default_config = json.loads(await response.text())
                merged = merge_config(default_config, current_config)
                await CONFIG.update(merged)

        except aiohttp.ClientError as e:
            print(f"Error fetching remote config: {e}")

    # asyncio.create_task(window.do_async_task())
    await asyncio.sleep(0)

def main():
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(os.path.join(DIRECTORY, "assets/icon.ico")))
        font = QFont("Roboto", 12)
        font.setBold(True)
        app.setFont(font)

        window = MainWindow()
        Pages.instigate(window)  # <- pass window here

        for obj in vars(Pages).values():
            if isinstance(obj, Page):
                window.stack.addWidget(obj)

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
