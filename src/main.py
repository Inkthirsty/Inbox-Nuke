import aiohttp, aiofiles, asyncio, sys, json, os, shutil, re, inspect, time
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
    QScrollArea, QCheckBox, QSpinBox, QSlider, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QTimer, QRegularExpression, QByteArray
from PySide6.QtGui import QColor, QMouseEvent, QFont, QIcon, QCursor, QRegularExpressionValidator, QValidator, QPixmap, QPainter, QBrush
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

async def set_pixmap(label: QLabel, source: str, width=None, height=None, radius: int | float = 0):
    pixmap = QPixmap()

    if os.path.exists(source):
        pixmap.load(source)
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get(source) as response:
                img_bytes = await response.read()
        pixmap.loadFromData(QByteArray(img_bytes))

    if width and height:
        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    if radius:
        size = pixmap.size()
        rounded = QPixmap(size)
        rounded.fill(Qt.GlobalColor.transparent)

        if 0 < radius < 1:
            radius = min(size.width(), size.height()) * radius

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(pixmap))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRect(0, 0, size.width(), size.height()), radius, radius)
        painter.end()
        pixmap = rounded

    label.setPixmap(pixmap)

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

    def hide(self):
        for w in self.widgets:
            w.hide()
        # Update the layout of the parent container
        if self.widgets:
            parent = self.widgets[0].parentWidget()
            if parent and parent.layout():
                parent.updateGeometry()

    def show(self):
        for w in self.widgets:
            w.show()
        # Update the layout of the parent container
        if self.widgets:
            parent = self.widgets[0].parentWidget()
            if parent and parent.layout():
                parent.updateGeometry()

    def add(self, *widgets):
        for w in widgets:
            self.widgets.append(w)

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
            self.components.heading = QLabel("Inbox Nuke")
            self.components.heading.setStyleSheet("font-size: 20pt")
            self.components.heading2 = QLabel("made by max (@inkthirsty)")
            self.components.heading2.setStyleSheet("padding-bottom: 10px;font-size: 10pt;font-weight: normal")

            """
            self.components.input = QLineEdit("Type something here")
            self.components.input.setFixedSize(*input_size)
            """

            self.components.button = QPushButton("Nuke", flat=True)
            self.components.button.setFixedSize(*button_size)
            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Nuke)))

            self.components.button2 = QPushButton("Settings (Coming soon maybe)", flat=True)
            self.components.button2.setFixedSize(*button_size)

            self.components.button3 = QPushButton("Credits (Coming soon idk)", flat=True)
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
            self.nuking = False
            self.progress = 0
            self.total = 0
            self.boxes = {}
            self.stats = {}

            default_align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
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

            # section 2
            
            self.components.heading3 = QLabel()
            self.components.heading3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.components.heading3.setStyleSheet("font-size: 18pt")

            self.components.label1 = QLabel()
            self.components.label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.components.label1.setStyleSheet("font-size: 10pt")
            
            self.components.progress = QProgressBar()
            self.components.progress.setFixedWidth(input_size[0])
            self.components.progress.setRange(0, 100)
            self.components.progress.setValue(0)

            group1 = WidgetGroup(self.components.heading, self.components.heading1, self.components.heading2, self.components.input1, self.components.button, self.components.checkbox, self.components.slider, self.components.spinbox)
            group2 = WidgetGroup(self.components.heading3, self.components.label1, self.components.progress)

            async def launch_nuke():
                if self.nuking:
                    return
                self.nuking = True

                async def update_progress():
                    while self.nuking:
                        self.components.progress.setValue((self.progress / self.total * 100))
                        self.components.progress.setFormat(f"{self.progress:,}/{self.total:,}")
                        await asyncio.sleep(0)

                for box in self.boxes.values():
                    box.setParent(None)
                    box.deleteLater()
                self.boxes.clear()
                self.stats.clear()

                async with aiohttp.ClientSession() as session:
                    endpoints = {hasattr(cls, "name") and getattr(cls, "name") or name: cls(session) for name, cls in vars(Endpoints).items() if inspect.isclass(cls)}
                    variants = choices.variants[:self.components.slider.value()]
                    self.progress = 0
                    self.total = len(variants)*len(endpoints)

                    asyncio.create_task(update_progress())

                    self.components.heading3.setText(f"Launching {self.total:,} virtual nukes")
                    self.components.label1.setText(choices.email)
                    group1.hide()
                    group2.show()

                    for endpoint in endpoints.values():
                        name = hasattr(endpoint, "name") and getattr(endpoint, "name") or "?"
                        icon = hasattr(endpoint, "icon") and getattr(endpoint, "icon") or "https://i.ibb.co/35gTZFC0/question-mark-4x.png"

                        box = QWidget(parent=self)
                        box.setFixedSize(300, 85)
                        box.setStyleSheet(f"""
                            background: transparent;
                            border: 2px solid {COLOR_THEME};
                            border-radius: 6px;
                        """)

                        box.box_image = QLabel(parent=box)
                        box.box_image.setGeometry(10, 10, 20, 20)
                        box.box_image.setStyleSheet(f"""background: transparent;border: none;border-radius: 25%;""")
                        asyncio.create_task(set_pixmap(box.box_image, icon, 20, 20, 0.25))
                        box.box_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

                        box.box_title = QLabel(name, parent=box)
                        box.box_title.setGeometry(35, 10, 265, 20)  # x, y, width, height
                        box.box_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        box.box_title.setStyleSheet(f"""background: transparent;border: none;border-radius: 25%;""")
            
                        box.box_progress = QProgressBar(parent=box)
                        box.box_progress.setGeometry(10, 35, 280, 40)
                        box.box_progress.setRange(0, 100)
                        box.box_progress.setValue(0)
                        box.box_progress.setFormat("Waiting...")

                        self.boxes[endpoint] = box
                        self.stats[endpoint] = []
                        layout.addWidget(box, alignment=default_align)
                    group2.add(*self.boxes.values())

                    tasks = []
                    for variant in variants:
                        for endpoint in endpoints.values():
                            tasks.append((endpoint, variant))

                    semaphore = asyncio.Semaphore(10)

                    async def wrap_endpoint(endpoint, variant):
                        box = self.boxes.get(endpoint)
                        stats = self.stats.get(endpoint)
                        async with semaphore:
                            try:
                                result = await endpoint(variant)
                                stats.append(result)
                                stats.count(True)
                                successful = stats.count(True)
                                attempts = len(stats)
                                box.box_progress.setValue(attempts/len(variants)*100)
                                box.box_progress.setFormat(f"{successful:,}/{attempts:,}｜{round(successful/attempts*100, 1)}%")
                                return result
                            finally:
                                self.progress += 1

                    tasks = [wrap_endpoint(endpoint, variant) for endpoint, variant in tasks]
                    await asyncio.gather(*tasks)
                self.nuking = False
                
            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(launch_nuke()))
            
            custom_align = {}

            # finalize
            for widget in self.components.iter_widgets():
                layout.addWidget(widget, alignment=custom_align.get(widget, default_align))
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
            
            group2.hide()

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
