import aiohttp, aiofiles, asyncio, sys, json, os, shutil, re
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
    QScrollArea, QCheckBox, QSpinBox, QSlider
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QTimer, QRegularExpression
from PySide6.QtGui import QColor, QMouseEvent, QFont, QIcon, QCursor, QRegularExpressionValidator, QValidator
from qasync import QEventLoop
from collections.abc import MutableMapping
from itertools import combinations
from endpoints import Endpoints

DIRECTORY = os.path.dirname(__file__)

CONFIG_FILENAME = "config.json"
CONFIG_PATH = os.path.join(DIRECTORY, CONFIG_FILENAME)

TEMP_PATH = os.path.join(DIRECTORY, "temp")
if os.path.exists(TEMP_PATH):
    shutil.rmtree(TEMP_PATH)
os.makedirs(TEMP_PATH, exist_ok=True)

TITLE = "Inbox Nuke"
VERSION = "1.0.0"

COLOR_1 = "#0a0a0a"
COLOR_2 = "#162034"
COLOR_THEME = "#386a8a"
COLOR_BORDER = "#555555"

COLOR_GREEN = "#7fff4d"
COLOR_RED = "#FF4D4D"

REQUIRED = f"<span style=\"color:{COLOR_RED}\">*</span>"

with open("style.css", "r") as file:
    style = file.read()
style = style.replace("{focus_color}", COLOR_THEME)
style = style.replace("{COLOR_1}", COLOR_1)
style = style.replace("{COLOR_2}", COLOR_2)
style_main = style.replace("{color}", COLOR_BORDER)

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

class WidgetGroup:
    def __init__(self, *widgets):
        self.widgets = list(widgets)
        self._visibility = {w: w.isVisible() for w in widgets}

    def hide(self):
        for w in self.widgets:
            w.hide()

    def show(self):
        for w in self.widgets:
            # restore previous state
            if self._visibility.get(w, True):
                w.show()
            else:
                w.hide()

    def add(self, *widgets):
        for w in widgets:
            self.widgets.append(w)
            self._visibility[w] = w.isVisible()

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
            self.components.heading.setStyleSheet("font-size: 20pt")
            self.components.heading2 = QLabel("made by max (@inkthirsty)")
            self.components.heading2.setStyleSheet("padding-bottom: 10px;font-size: 10pt;font-weight: normal")

            """
            self.components.input = QLineEdit("Type something here")
            self.components.input.setFixedSize(*input_size)
            """

            self.components.button = QPushButton("Nuke France", flat=True)
            self.components.button.setFixedSize(*button_size)
            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Nuke)))

            self.components.button2 = QPushButton("Kick a toddler", flat=True)
            self.components.button2.setFixedSize(*button_size)

            self.components.button3 = QPushButton("Commit tax evasion", flat=True)
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


            
    class Nuke(Page):
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
            layout.setSpacing(10)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # do important stuff under here

            class choices: pass

            self._init_callbacks = []

            def wrap(signal, callback):
                def new_callback():
                    callback()
                    check()
                signal.connect(new_callback)
                self._init_callbacks.append(callback)

            self.components.heading = QLabel("Nuke your inbox!")
            self.components.heading.setStyleSheet("padding-bottom: 10px;font-size: 20pt")

            self.components.heading1 = QLabel(f"Email {REQUIRED}")
            self.components.heading1.setFixedWidth(input_size[0])

            validator = QRegularExpressionValidator(QRegularExpression(r"(^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*$)"))

            def dot_variants(email: str) -> list[str]:
                try:
                    local, domain = email.split("@", 1)
                except ValueError:
                    return [email]
                
                if not re.fullmatch(r"[A-Za-z0-9]+", local):
                    return [email]
                
                results = set()
                n = len(local)
                
                positions = range(1, n)
                for r in range(len(positions) + 1):
                    for combo in combinations(positions, r):
                        parts = []
                        last = 0
                        for pos in combo:
                            parts.append(local[last:pos])
                            last = pos
                        parts.append(local[last:])
                        dotted = ".".join(parts)
                        results.add(f"{dotted}@{domain}")
                
                return list(reversed(sorted(results)))

            def check_email():
                text = str(self.components.input1.text()).strip().split(" ")[0]
                state, _, _ = validator.validate(text, 0)
                acceptable = state == QValidator.State.Acceptable
                choices.email = acceptable and text.lower() or None
                self.components.input1.setStyleSheet(style.replace("{color}", len(text) > 0 and (acceptable and COLOR_GREEN or COLOR_RED) or COLOR_BORDER))

                choices.variants = acceptable and dot_variants(choices.email) or None
                variantCount = choices.variants and len(choices.variants) or 1
                self.components.heading2.setText(f"Threads (1 - {variantCount:,})")
                self.components.spinbox.setMaximum(variantCount)
                self.components.slider.setMaximum(variantCount)
                return acceptable

            self.components.input1 = QLineEdit(placeholderText="Input email here", maxLength=100)
            self.components.input1.setFixedSize(*input_size)
            wrap(self.components.input1.textChanged, check_email)

            """
            self.components.label1 = QLabel(f"small :3")
            self.components.label1.setStyleSheet("padding-top: -6px;font-size: 8pt")
            self.components.label1.setFixedSize(input_size[0], 20)
            self.components.label1.hide()
            """

            self.components.heading2 = QLabel()
            self.components.heading2.setFixedWidth(input_size[0])

            self.components.slider = QSlider(Qt.Orientation.Horizontal)
            self.components.slider.setMinimum(1)
            self.components.slider.setMaximum(1)
            self.components.slider.setTickInterval(10)
            self.components.slider.setFixedWidth(input_size[0])
            self.components.slider.setTickPosition(QSlider.TickPosition.NoTicks)

            self.components.spinbox = QSpinBox()
            self.components.spinbox.setFixedWidth(input_size[0])
            self.components.spinbox.setMinimum(1)
            self.components.spinbox.setMaximum(1)
            
            self.components.slider.valueChanged.connect(self.components.spinbox.setValue)
            self.components.spinbox.valueChanged.connect(self.components.slider.setValue)
            
            def check_agreement():
                agreed = self.components.checkbox.checkState() == Qt.CheckState.Checked
                choices.agreed = agreed
                check()
                return agreed

            self.components.checkbox = QCheckBox("I agree to use this tool only on my own email inboxes and not to\nmisuse it with the intent to cause damage.")
            self.components.checkbox.setFixedWidth(input_size[0])
            wrap(self.components.checkbox.stateChanged, check_agreement)

            self.components.button = QPushButton("Launch Nuke!")
            self.components.button.setFixedSize(*button_size)
            self.components.button.setEnabled(False)

            def check():
                criteria = [choices.email, choices.agreed, ]
                self.components.button.setEnabled(all(criteria))

            custom_align = {}

            group1 = WidgetGroup(self.components.heading1, self.components.input1, self.components.button, self.components.checkbox)

            # finalize
            for widget in self.components.iter_widgets():
                layout.addWidget(widget, alignment=custom_align.get(widget, Qt.AlignmentFlag.AlignHCenter))
            for callback in self._init_callbacks:
                callback()

            # back button
            back_button = QPushButton("Back", self, flat=True)
            back_button.setFixedHeight(30)
            back_button.adjustSize()
            back_button.move(10, 10)
            back_button.raise_()
            back_button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Home)))

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
        self.setStyleSheet(style_main)

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
        font = QFont("Nunito", 12)
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
