import aiohttp, aiofiles, asyncio, sys, json, os, shutil, re, inspect, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QStackedWidget,
    QPushButton, QScrollArea,
    QCheckBox, QSpinBox, QSlider, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QRect, QByteArray, QRegularExpression
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QRegularExpressionValidator, QValidator
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
VERSION = "1.4"

COLOR_1 = "#0a0a0a"
COLOR_2 = "#162034"
COLOR_THEME = "#386a8a"
COLOR_BORDER = "#555555"
COLOR_GREEN = "#7fff4d"
COLOR_RED = "#FF4D4D"
REQUIRED = f"<span style=\"color:{COLOR_RED}\">*</span>"

STYLE_PATH = os.path.join(DIRECTORY, "assets/style.css")

with open(STYLE_PATH, "r") as file:
    style = file.read()
style = style.replace("{focus_color}", COLOR_THEME).replace("{COLOR_1}", COLOR_1).replace("{COLOR_2}", COLOR_2)
style_main = style.replace("{color}", COLOR_BORDER)

# ----------------- Async Helpers -----------------
async def get_favicon(url: str) -> str:
    params = {"client": "SOCIAL", "type": "FAVICON", "fallback_opts": "TYPE,SIZE,URL", "size": "256", "url": url}
    async with aiohttp.ClientSession() as session:
        async with session.head("https://t3.gstatic.com/faviconV2", params=params) as response:
            return response.ok and str(response.url) or None

async def set_pixmap(label: QLabel, source: str, width=None, height=None, radius: float = 0):
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

    try:
        label.setPixmap(pixmap)
    except RuntimeError:
        pass  # deleted QLabel

def safe_delete(widget):
    """Delete QWidget safely."""
    try:
        widget.setParent(None)
        widget.deleteLater()
    except RuntimeError:
        pass

def safe_show(widget):
    try:
        widget.show()
    except RuntimeError:
        pass

def safe_hide(widget):
    try:
        widget.hide()
    except RuntimeError:
        pass

# ----------------- Page Classes -----------------
class Page(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self._init_widgets()

    def _init_widgets(self):
        pass

    async def on_show(self):
        pass

    async def on_hide(self):
        pass

    def reset(self):
        for i in reversed(range(self.layout().count() if self.layout() else 0)):
            item = self.layout().takeAt(i)
            widget = item.widget()
            if widget:
                safe_delete(widget)
        self._init_widgets()

class Components:
    def __init__(self):
        self._order = []
        self._widgets = {}

    def __setattr__(self, name, value):
        if isinstance(value, QWidget):
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
            safe_hide(w)
        if self.widgets and self.widgets[0].parentWidget() and self.widgets[0].parentWidget().layout():
            self.widgets[0].parentWidget().updateGeometry()

    def show(self):
        for w in self.widgets:
            safe_show(w)
        if self.widgets and self.widgets[0].parentWidget() and self.widgets[0].parentWidget().layout():
            self.widgets[0].parentWidget().updateGeometry()

    def add(self, *widgets):
        self.widgets.extend(widgets)

class Pages:
    class Home(Page):
        def _init_widgets(self):
            margins = (0,0,0,0)
            button_size = (300,40)
            input_size = (400,30)

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

            self.components.heading = QLabel("Inbox Nuke")
            self.components.heading.setStyleSheet("font-size: 20pt")
            self.components.heading2 = QLabel("made by max (@inkthirsty)")
            self.components.heading2.setStyleSheet("padding-bottom: 10px;font-size: 10pt;font-weight: normal")

            self.components.button = QPushButton("Nuke", flat=True)
            self.components.button.setFixedSize(*button_size)
            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Nuke)))

            self.components.button2 = QPushButton("Settings (Coming soon maybe)", flat=True)
            self.components.button2.setFixedSize(*button_size)
            self.components.button3 = QPushButton("Credits (Coming soon idk)", flat=True)
            self.components.button3.setFixedSize(*button_size)

            custom_align = {}
            for widget in self.components.iter_widgets():
                layout.addWidget(widget, alignment=custom_align.get(widget, Qt.AlignmentFlag.AlignHCenter))

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)

        async def do_async_button(self):
            self.components.button.setEnabled(False)
            await asyncio.sleep(3)
            self.components.button.setEnabled(True)

    class Nuke(Page):
        def _init_widgets(self):
            self.nuking = False
            self.progress = 0
            self.total = 0
            self.boxes = {}
            self.stats = {}
            self._nuke_tasks = []

            default_align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
            margins = (0,0,0,0)
            button_size = (250,40)
            input_size = (400,30)

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

            validator = QRegularExpressionValidator(QRegularExpression(
                r"(^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*$)"))

            def dot_variants(email: str) -> list[str]:
                try:
                    local, domain = email.split("@",1)
                except ValueError: return [email]
                if not re.fullmatch(r"[A-Za-z0-9]+", local):
                    return [email]
                results = set()
                positions = range(1,len(local))
                for r in range(len(positions)+1):
                    for combo in combinations(positions,r):
                        parts = []
                        last = 0
                        for pos in combo:
                            parts.append(local[last:pos])
                            last = pos
                        parts.append(local[last:])
                        results.add(f"{'.'.join(parts)}@{domain}")
                return list(reversed(sorted(results)))

            def check_email():
                text = str(self.components.input1.text()).strip().split(" ")[0]
                state, _, _ = validator.validate(text, 0)
                acceptable = state == QValidator.State.Acceptable
                choices.email = acceptable and text.lower() or None
                self.components.input1.setStyleSheet(
                    style.replace("{color}", len(text) > 0 and (acceptable and COLOR_GREEN or COLOR_RED) or COLOR_BORDER))
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

            self.components.checkbox = QCheckBox(
                "I agree to use this tool only on my own email inboxes and not to\nmisuse it with the intent to cause damage."
            )
            self.components.checkbox.setFixedWidth(input_size[0])
            wrap(self.components.checkbox.stateChanged, check_agreement)

            self.components.button = QPushButton("Launch Nukes!")
            self.components.button.setFixedSize(*button_size)
            self.components.button.setEnabled(False)

            def check():
                criteria = [choices.email, choices.agreed]
                self.components.button.setEnabled(all(criteria))

            # Section 2
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

            self.components.stop_button = QPushButton("Stop Nukes!")
            self.components.stop_button.setFixedSize(*button_size)

            group1 = WidgetGroup(self.components.heading, self.components.heading1, self.components.heading2,
                                 self.components.input1, self.components.button, self.components.checkbox,
                                 self.components.slider, self.components.spinbox)
            group2 = WidgetGroup(self.components.heading3, self.components.label1,
                                 self.components.stop_button, self.components.progress)

            # ----------------- Async Nuking -----------------
            async def stop_nuke():
                if self.nuking:
                    self.nuking = False
                    self.components.stop_button.setText("Return")
                    for task in self._nuke_tasks: task.cancel()
                    self._nuke_tasks.clear()
                else:
                    group2.hide()
                    group1.show()
                    for box in list(self.boxes.values()):
                        safe_delete(box)
                    self.boxes.clear()
                    self.components.stop_button.setText("Stop Nukes!")

            self.components.stop_button.clicked.connect(lambda checked=False: asyncio.create_task(stop_nuke()))

            async def launch_nuke():
                if self.nuking: return
                self.nuking = True

                async def update_progress():
                    while self.nuking:
                        try:
                            self.components.progress.setValue((self.progress / self.total * 100))
                            self.components.progress.setFormat(f"{self.progress:,}/{self.total:,}")
                        except RuntimeError:
                            pass
                        if self.progress >= self.total:
                            break  # exit when done
                        await asyncio.sleep(0)

                for box in list(self.boxes.values()):
                    safe_delete(box)
                self.boxes.clear()
                self.stats.clear()

                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    endpoints = {getattr(cls, "name", name): cls(session) for name, cls in vars(Endpoints).items() if inspect.isclass(cls)}
                    endpoints = dict(random.sample(list(endpoints.items()), len(endpoints)))

                    variants = choices.variants[:self.components.slider.value()]
                    self.progress = 0
                    self.total = len(variants) * len(endpoints)
                    asyncio.create_task(update_progress())

                    self.components.heading3.setText(f"Launching {self.total:,} virtual nukes")
                    self.components.label1.setText(choices.email)
                    group1.hide()
                    group2.show()

                    # Create boxes safely
                    for endpoint in endpoints.values():
                        if not self.nuking: break
                        name = getattr(endpoint, "name", "?")
                        icon = getattr(endpoint, "icon", None) or (hasattr(endpoint,"url") and await get_favicon(endpoint.url)) or "https://i.ibb.co/35gTZFC0/question-mark-4x.png"

                        box = QWidget(parent=self)
                        box.setFixedSize(300,85)
                        box.setStyleSheet(f"background: transparent; border: 2px solid {COLOR_THEME}; border-radius: 6px;")

                        box.box_image = QLabel(parent=box)
                        box.box_image.setGeometry(10,10,20,20)
                        box.box_image.setStyleSheet("background: transparent; border: none;")
                        asyncio.create_task(set_pixmap(box.box_image, icon, 20, 20, 0.1))
                        box.box_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

                        box.box_title = QLabel(name,parent=box)
                        box.box_title.setGeometry(35,10,265,20)
                        box.box_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        box.box_title.setStyleSheet("background: transparent; border: none; border-radius: 25%")

                        box.box_progress = QProgressBar(parent=box)
                        box.box_progress.setGeometry(10,35,280,40)
                        box.box_progress.setRange(0,100)
                        box.box_progress.setValue(0)
                        box.box_progress.setFormat("Waiting...")

                        self.boxes[endpoint] = box
                        self.stats[endpoint] = []
                        layout.addWidget(box, alignment=default_align)

                    group2.add(*self.boxes.values())

                    queue = asyncio.Queue()
                    for variant in variants:
                        for endpoint in endpoints.values():
                            queue.put_nowait((endpoint, variant))

                    async def worker():
                        while self.nuking:
                            try:
                                endpoint, variant = queue.get_nowait()
                            except asyncio.QueueEmpty: break
                            box = self.boxes.get(endpoint)
                            stats = self.stats.get(endpoint)
                            try:
                                result = await endpoint(variant)
                                stats.append(result)
                                successful = stats.count(True)
                                attempts = len(stats)
                                try:
                                    box.box_progress.setValue(attempts/len(variants)*100)
                                    box.box_progress.setFormat(f"Rate: {round(successful/attempts*100)}% ({successful:,}/{attempts:,})")
                                except RuntimeError: pass
                            except asyncio.CancelledError:
                                return
                            finally:
                                self.progress += 1
                                queue.task_done()

                    self._nuke_tasks = [asyncio.create_task(worker()) for _ in range(10)]
                    try:
                        await queue.join()
                    finally:
                        await stop_nuke()
                        self.nuking = False
                        for w in self._nuke_tasks:
                            w.cancel()

            self._current_nuke_task: asyncio.Task | None = None  # add this above

            async def launch_nuke_wrapper():
                # cancel any previous running nuke
                if self._current_nuke_task and not self._current_nuke_task.done():
                    self._current_nuke_task.cancel()
                    try:
                        await self._current_nuke_task
                    except asyncio.CancelledError:
                        pass
                self._current_nuke_task = asyncio.create_task(launch_nuke())

            self.components.button.clicked.connect(lambda checked=False: asyncio.create_task(launch_nuke_wrapper()))


            custom_align = {}
            for widget in self.components.iter_widgets():
                layout.addWidget(widget, alignment=custom_align.get(widget, default_align))
            for callback in self._init_callbacks:
                callback()

            back_button = QPushButton("Back", self, flat=True)
            back_button.setFixedHeight(30)
            back_button.adjustSize()
            back_button.move(10,10)
            back_button.raise_()
            back_button.clicked.connect(lambda checked=False: asyncio.create_task(self.window.switchPage(Pages.Home)))

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(scroll)
            group2.hide()

    @classmethod
    def instigate(cls, window):
        for name, page_cls in vars(cls).items():
            if isinstance(page_cls,type) and issubclass(page_cls,Page) and page_cls is not Page:
                setattr(cls,name,page_cls(window))

# ----------------- Main Window -----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{TITLE} v{VERSION}")
        self.setMinimumSize(740,460)
        self.resize(740,460)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowIcon(QIcon(os.path.join(DIRECTORY,"assets/icon.ico")))
        self._setup_ui()
        self.apply_style()

    def _setup_ui(self):
        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.stack)
        for obj in vars(Pages).values():
            if isinstance(obj,Page):
                self.stack.addWidget(obj)

    def apply_style(self):
        self.setStyleSheet(style_main)

    async def switchPage(self,page: Page):
        current = self.getPage()
        if current and hasattr(current,"on_hide"):
            await current.on_hide()
        if self.getPage() != page:
            self.stack.setCurrentWidget(page)
            if hasattr(page,"on_show"):
                await page.on_show()

    def getPage(self) -> Page:
        return self.stack.currentWidget()

# ----------------- Async Config -----------------
class AsyncSynchronizedDict(MutableMapping):
    def __init__(self, filename):
        self.filename = filename
        self.data = {}

    def __getitem__(self, key): return self.data[key]
    async def __setitem__(self, key, value): self.data[key]=value; await self._write_to_file()
    async def __delitem__(self, key): del self.data[key]; await self._write_to_file()
    def __iter__(self): return iter(self.data)
    def __len__(self): return len(self.data)
    def __contains__(self, key): return key in self.data
    def keys(self): return self.data.keys()
    def values(self): return self.data.values()
    def items(self): return self.data.items()
    def get(self,key,default=None): return self.data.get(key,default)
    def as_dict(self): return self.data
    async def load(self):
        try:
            if not os.path.exists(self.filename): raise FileNotFoundError
            async with aiofiles.open(self.filename,'r') as f: content = await f.read()
            self.data = json.loads(content)
        except (FileNotFoundError,json.JSONDecodeError): self.data={}
    async def _write_to_file(self):
        async with aiofiles.open(self.filename,'w') as f:
            await f.write(json.dumps(self.data,indent=4))
    async def update(self,other=None,**kwargs):
        if other is None: other={}
        elif isinstance(other,AsyncSynchronizedDict): other=other.data
        elif not isinstance(other,dict): raise TypeError("update() expects dict or AsyncSynchronizedDict")
        self.data.update(other,**kwargs)
        await self._write_to_file()
    def __repr__(self): return f"AsyncSynchronizedDict({self.data})"

def merge_config(default: dict, current: dict) -> dict:
    for key, value in default.items():
        if key not in current: current[key]=value
        elif isinstance(value,dict) and isinstance(current.get(key),dict): merge_config(value,current[key])
    return current

async def main_async(window):
    async with aiohttp.ClientSession() as session:
        CONFIG = AsyncSynchronizedDict(CONFIG_PATH)
        await CONFIG.load()
        current_config = CONFIG.as_dict()
        try:
            async with session.get(f"https://raw.githubusercontent.com/Inkthirsty/Inbox-Nuke/refs/heads/main/src/config.example.json") as response:
                response.raise_for_status()
                default_config = json.loads(await response.text())
                merged = merge_config(default_config,current_config)
                await CONFIG.update(merged)
        except aiohttp.ClientError as e: print(f"Error fetching remote config: {e}")

        try:
            async with session.get("https://raw.githubusercontent.com/Inkthirsty/Inbox-Nuke/refs/heads/main/latest.txt") as response:
                response.raise_for_status()
                latest = await response.text()
                if VERSION < latest:
                    window.setWindowTitle(f"{window.windowTitle()} (Newest: {latest})")
        except aiohttp.ClientError as e: print(f"Error fetching latest version: {e}")
    await asyncio.sleep(0)

def main():
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(os.path.join(DIRECTORY, "assets/icon.ico")))
        font = QFont("Roboto",12)
        font.setBold(True)
        app.setFont(font)

        window = MainWindow()
        Pages.instigate(window)

        for obj in vars(Pages).values():
            if isinstance(obj,Page):
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
