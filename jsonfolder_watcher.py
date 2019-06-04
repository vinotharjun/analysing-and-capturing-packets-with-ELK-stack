'''
the jsonfolder_watcher.py file that will act as watcher for the 'decodedfiles' folder 
that watches if any new json  has came ,if came it will get data from the newly came json file
and upload the data to the elastic search  

'''
#imports 
from setup_logger import logger as logging
import sys
import time

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from elasticsearch import Elasticsearch,helpers
from globaldata import decodedFolderName,logs
from globaldata import password,username,url,port

import os
import json
from pygrok import Grok
from multiprocessing import Pool
import multiprocessing as mp
import warnings
warnings.filterwarnings("ignore")
import re

types = {
    'WORD': r'\w+',
    'NUMBER': r'\d+',
    # todo: extend me
}


def compile(pat):
    return re.sub(r'%{(\w+):(\w+)}', 
        lambda m: "(?P<" + m.group(2) + ">" + types[m.group(1)] + ")", pat)
pattern ="m%{NUMBER:mitigation_id}_%{NUMBER:packet_status}_%{NUMBER:counter_measureid}_%{NUMBER:timestamp}n.pcap.json"
rr = compile(pattern)
#watcher class that will be dispatched when changes occurs in specified directory
class Watcher():
    
   #helper function to conncet the python file to elasticseach
    def connect_elasticsearch(self):
        _es = None
    #connect to the es
        _es = Elasticsearch([url],http_auth=(username, password),scheme="https", port=port, verify_certs=False)
    #es.ping that returns true if connected else it  will return false
        if _es.ping():
            #  print("connected")
            pass
            #  logging.info('Yay Connect')     
        else:
            pass
            #   logging.error('Awww it could not connect!')
        return _es 

    #dispatching when the folder changes somthing 
    def dispatch(self,event):
        #mulitiprocessing the dispacher
        p.apply_async(self.upload,args=(event,))
    def upload(self,event):
              
        #checking the event type when the user changes or modifies somthing in the specified folder
        #(event_type=created or modified or deleted)
        # event_type ="created"| src_path="path of the file"|
        es=self.connect_elasticsearch()
        if event.event_type=="created":
            file_to_be_uploaded=event.src_path
            packets = []
            
            
           
            try:
                
                #read the entire content from the json file
                os.chmod(file_to_be_uploaded, 0o777)
                main_name= os.path.basename(file_to_be_uploaded)
                file_details=re.search(rr,main_name).groupdict()
                # print(file_details)
                iter =0
                for line in open(file_to_be_uploaded,errors="ignore"):
                    packets.append(json.loads(line))
                    if iter%2==1:
                       packets[iter]["file_details"]=file_details
                    iter=iter+1
            
                extracted_name=os.path.basename(file_to_be_uploaded)
                
                response = es.bulk(packets)
                if response["errors"]:
                    with open("./"+logs+"/failiurelogs.txt", "a") as myfile:
                        myfile.write(file_to_be_uploaded+"\n")
                        myfile.close()
                    logging.error("fail:"+extracted_name)
                else:
                    
                    logging.info("success:"+extracted_name)
                #once the file has been uploaded to elasticsearch just delete the file in the decodedfiles directory
                #os.chmod(file_to_be_uploaded, 0o777)
                #os.remove(file_to_be_uploaded) 
            except Exception as e:
                logging.error("exception in importing to elasticsearch line 42")
                with open("./"+logs+"/failiurelogs.txt", "a") as myfile:
                        myfile.write(file_to_be_uploaded)
                        myfile.write(str(e)+"\n")
                        myfile.close()
                logging.info("fail:"+extracted_name)
if __name__ == "__main__":
    logging.info("json watcher")
    # logging.basicConfig(level=logging.INFO,
    #                     format='%(asctime)s - %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    path = decodedFolderName
    
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(logs):
        os.makedirs(logs)
    # elasticsearch connection 
    p = Pool(10)

    #main class 
    watcher = Watcher()
    #specifying observer
    observer = Observer()
    observer.schedule(watcher, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    