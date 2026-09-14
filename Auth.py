#libraries
import os
import secrets
from dotenv import load_dotenv
from urllib.parse import urlencode
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


#function definitions
def generate_code_verifier(): #generates a verifier to use when communicating with MAL
    return secrets.token_urlsafe(64)





#main code


load_dotenv() #loads .env file which contains client id, client secret and redurect URI

#gets secret MAL client details
CLIENT_ID = os.getenv("MAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET")
REDIRECT_URI = os.getenv("MAL_REDIRECT_URI")


code_verifier = generate_code_verifier()

#parameters used to communicate with MAL
parameters = {                      
    "response_type": "code", #ask MAL for an authorisation code
    "client_id": CLIENT_ID, 
    "redirect_uri": REDIRECT_URI,
    "code_challenge": code_verifier,
    "code_challenge_method": "plain", #Tells MAL how the code challenge was generated
}

#Gnerates a URL for MAL which includes all parameters which are url encoded, this tells MAL to begin the OAuth process with my parameters
auth_url = (
    "https://myanimelist.net/v1/oauth2/authorize?"
    + urlencode(parameters)
)



print(auth_url)
authorisation_code = None




class CallbackHandler(BaseHTTPRequestHandler):

    #function is run when browser makes a HTTP get request
    def do_GET(self):
        global authorisation_code

    
        #parse the url that MAL redirected to
        parsed_url = urlparse(self.path)

        #extract the query parameters into a dictionary
        query_params = parse_qs(parsed_url.query)

        #get the authorization code (stuff after code=)
        authorisation_code = query_params.get("code", [None])[0]

        if authorisation_code:
            print("Authorization code received!")
            

            #tell the browser everything worked
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(
                b"<h1>Authorization successful!</h1>"
                b"<p>You can close this window.</p>"
            )

        else:
            print("No authorization code found.")
            print("URL:", self.path)

            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(
                b"<h1>Authorization failed.</h1>"
                b"<p>No authorization code was found.</p>"
            )


#creates server to listen to localhost for authorisation code from MAL
server = HTTPServer(("localhost", 8000), CallbackHandler)

print("Waiting for MAL callback...")
server.handle_request()
server.server_close()

print("Code:", authorisation_code)

#getting a token from the MAL api
token_url = "https://myanimelist.net/v1/oauth2/token"

#data to give to API during token request
data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "authorization_code",
    "code": authorisation_code,
    "code_verifier": code_verifier,
    "redirect_uri": REDIRECT_URI,
}


response = requests.post(token_url, data=data)

#prints the status code of the request (200 is a success)
print("Status:", response.status_code)
print("Response:", response.text)

if response.status_code != 200:
    print("Token request failed.")
    exit()



#records token data
token_data = response.json()

access_token = token_data["access_token"]
refresh_token = token_data["refresh_token"]

#creates a HTTP header containing token data
headers = {
    "Authorization": f"Bearer {access_token}"
}

#test request to get anime id 1 from MAL API (cowboy bebop)
response = requests.get(
    "https://api.myanimelist.net/v2/anime/1",
    headers=headers
)

print(response.json())

