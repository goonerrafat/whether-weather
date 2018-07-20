import requests, json , os,re


def handle_weather(lattitue , longitude):
    dark_sky_key = os.getenv("DS_KEY")
    weather = requests.get("https://api.darksky.net/forecast/"+ dark_sky_key+ "/"+lattitue+","+lattitue).json()
    return json.dumps(weather["currently"], indent = 2)
 

def process_password(password , confirm_password):
    if(password != confirm_password):
        return False
    #check if the password have atleast a digit and a capital letter.power of regex!!
    if(re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,20}$", password)):
        return True
    return False