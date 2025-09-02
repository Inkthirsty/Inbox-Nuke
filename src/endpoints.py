import aiohttp

class Endpoint():
    def __init__(self):
        super().__init__()
        self._init_widgets()

    def _init_widgets(self):
        pass


class Endpoints:
    class Home(Endpoint):
        def _init_widgets(self):
            pass

        async def request(self, data: str):
            # get request to test.com
            self._init_widgets()

    @classmethod
    def instigate(cls):
        for name, page_cls in vars(cls).items():
            if isinstance(page_cls, type) and issubclass(page_cls, Endpoint):
                setattr(cls, name, page_cls())