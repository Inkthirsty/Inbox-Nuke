import aiohttp

class Endpoint:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

class Endpoints:
    class Home(Endpoint):
        async def __call__(self, email: str):
            data = {
                "publicationIds": "458709,10845,556800,329241,35345,471923,737237",
                "email": email
            }
            async with self.session.post("https://substack.com/api/v1/reader/signup/just_email", json=data) as response:
                resp = await response.text()
                print("RESP:", resp)
            return response