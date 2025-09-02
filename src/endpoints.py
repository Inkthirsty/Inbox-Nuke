class Endpoint:
    def __init__(self, session):
        self.session = session

class Endpoints:
    class Home(Endpoint):
        async def request(self, data: str):
            async with self.session.get(f'https://test.com/{data}') as response:
                response.raise_for_status()
                response_text = await response.text()
                print(f"Request to https://test.com/{data} successful. Status: {response.status}")
                return response_text