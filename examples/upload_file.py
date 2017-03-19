from domino import Domino
import os

output_dir = "results"

# connect to domino; be sure to have these environment variables set
#  (runs inside a Domino executor automatically set these for you)
domino = Domino("marks/test",
                api_key=os.environ['DOMINO_USER_API_KEY'],
                host=os.environ['DOMINO_API_HOST'])

f = open('numbers.csv', 'rb')
r = domino.files_upload("/a_new_folder/a_new_file.csv", f)

if r.status_code == 201:
    print(":) Upload successful")
else:
    print("!! Upload failed")
