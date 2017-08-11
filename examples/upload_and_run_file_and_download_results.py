#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
 
# USAGE:
#    python uploader.py -k <secret_key> -u https://vip.domino.tech -p "ianmichell/quick-start" -f input.txt -r "filewriter.py input.txt -o output.txt" -o output -R results
#    (-o is treated as a directory if there are multiple results found by matching -R)


from domino import Domino
import os
import argparse
import time
import re
 
CHUNK_SIZE = 16 * 1024
UPLOAD_DIR = os.getenv('UPLOAD_DIR', '')
API_KEY = os.environ.get('DOMINO_USER_API_KEY')
URL = os.environ.get('DOMINO_API_URL')
PROJECT = os.environ.get('DOMINO_PROJECT')
RUN = os.environ.get('DOMINO_RUN')
 
# Upload the specified file to domino
def upload_file(domino, dest, file):
    with open(file, 'r') as f:
        r = domino.files_upload(dest + '/' + file, f)
        return r.status_code
 
# Execute the specified run on domino
def execute_run(domino, run):
    # Execute the run
    result = domino.runs_start(run.split())
 
    # get the run id
    run_id = result.get("runId")
 
    return run_id
 
# Check execution status of run
def check_status(domino, run_id):
    return domino.runs_status(run_id)
 
def download_results(domino, commitId, results, output, exp):
    download = []
    files = domino.files_list(commitId)
    for file in files['data']:
        pattern = None
        if results is None and exp != None:
            pattern = re.compile(exp)
        else:
            # Remove any "/" from start of path
            results = re.sub(r"^/*", "", results)
            # Regex match all the files in the list
            pattern = re.compile("^" + results + "*")
        # Run a match
        match = pattern.match(file['path'])
        if match:
            download.append(file)
 
    if len(download) == 0:
        print("Nothing to download")
        return
 
    if output is None:
        output = ""
 
    for d in download:
        url = domino.blobs_get(d['key'])
        file_to_write = ""
 
        # if we have multiple files, then output is a directory
        if output and len(download) > 1:
            file_to_write = output + "/" + re.sub("^" + results + "/?", "", d['path'])
            if not os.path.exists(os.path.dirname(file_to_write)):
                os.makedirs(os.path.dirname(file_to_write))
        # otherwise it's just a file
        elif output:
            file_to_write = output
 
        # write the contents of the url request to the new file
        print("Downloading: " + file_to_write)
        with open(file_to_write, "wb") as f:
            while True:
                chunk = url.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
 
# domino = Domino(PROJECT, API_KEY, HOST)
if __name__ == "__main__":
 
    # input arguments
    parser = argparse.ArgumentParser(description='Upload a file to domino')
    parser.add_argument('-k', '--api-key', dest='api_key', default=API_KEY, help='Your user API key', required=True)
    parser.add_argument('-u', '--api-url', dest='url', default=URL, help='Your domino url', required=True)
    parser.add_argument('-f', '--file', dest='file', help='File to upload', required=True)
    parser.add_argument('-p', '--project', dest='project', default=PROJECT, help='Project', required=True)
    parser.add_argument('-d', '--dest', dest='dest', default=UPLOAD_DIR, help='Upload destination with the project')
    parser.add_argument('-r', '--run', dest='run', default=RUN, help='Batch process to run')
    parser.add_argument('-R', '--results', dest='results', help='The results to download', required=False)
    parser.add_argument('-e', '--expression', dest='expression', help='Results expression', required=False)
    parser.add_argument('-o', '--output', dest='output', help="The output of the results (default results)", required=False)
    parser.add_argument('-i', '--interval', type=int, dest='interval', default=1, help="Poll interval for the run status")
    args = parser.parse_args()
 
    # Create domino instance
    domino = Domino(args.project, api_key=args.api_key, host=args.url)
 
    # upload the file
    status = upload_file(domino, args.dest, args.file)
 
    if status != 201:
        raise "Upload failed with status code: " + status
 
    print("File uploaded successfully. Executing run: " + args.run)
    run_id = execute_run(domino, args.run)
 
    # Poll domino for run execution status and sleep for the specified interval
    print("Waiting for run to complete")
    run = check_status(domino, run_id)
    while run['completed'] == None:
        time.sleep(args.interval)
        run = check_status(domino, run_id)
 
    # Make sure the run succeeded... If not then throw an error
    if run['status'] != 'Succeeded':
        print("Run failed with status: " + run['status'])
        exit(1)
 
    commitId = run['outputCommitId']
 
    print("Run completed with commitId: " + commitId)
    # Download results (if the path is specified)
    if args.results != None or args.expression != None:
        print("Downloading results")
        download_results(domino, commitId, args.results, args.output, args.expression)
        print("Done")
