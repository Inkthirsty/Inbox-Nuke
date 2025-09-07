import aiohttp, time

class Endpoint:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

PASSWORD = """T)v5q(`'<>2iP29X8a+N"""

class Endpoints:
    class FalconComputers(Endpoint):
        name = "Falcon Computers"
        icon = "https://i.ibb.co/RZWx1Nk/5f89d6523a2a.png"
        async def __call__(self, email: str):
            data = {
                "email": email,
                "confirmemail": email,
                "password": PASSWORD,
                "confirmpassword": PASSWORD
            }
            async with self.session.post("https://www.falconcomputers.co.uk/myaccount/register", data=data, allow_redirects=False) as response:
                return response.status == 302
            
    class altontowers(Endpoint):
        name = "Alton Towers"
        icon = "https://i.ibb.co/7NLKZzHx/image.png"
        async def __call__(self, email: str):
            data = {
                "__RequestVerificationToken": "",
                "Language": "en",
                "Attraction": "PAT",
                "Campaign": "brandsite",
                "Source": "Website",
                "SourceDetail": "www.altontowers.com/sign-up/",
                "ConsentType": "Merlin Global",
                "FallbackCountry": "GB",
                "EnableRecaptcha": "False",
                "Email": email,
                "FirstName": str(time.time()),
                "Lastname": str(time.time()),
                "Permission": "on",
            }
            async with self.session.post("https://www.altontowers.com/umbraco/api/signupform/submit", json=data) as response:
                return response.ok # it returns 200 even if it doesnt send so idk
            