from domino import Domino
import os

domino = Domino("marks/quick-start-fork",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

if domino.endpoint_publish("main.py", "api_endpoint",
                           "22d864481c66b36d676056905d1f0545f5d3b742"):
    print("API endpoint published!")
else:
    print("API endpoint could not be published")
