

#imports 
import sys
import time

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from globaldata import pcapFolderName,tempDecodedFolderName,decodedFolderName
import os
import re
from multiprocessing import Pool
import multiprocessing as mp
import shutil
from setup_logger import logger
# create logger


#

class Watcher():

    def decode_pcap(self,filename):
       
        
        extracted_name=os.path.basename(filename)
        json_filename=tempDecodedFolderName+"/"+extracted_name+".json"
        movable=decodedFolderName+"/"+extracted_name+".json"
        os.system("tshark -r "+filename+" -T ek >"+json_filename)
        os.rename(json_filename,movable)

        logger.info(extracted_name+": decoded successfully")
        #os.chmod(filename, 0o777)
        #os.remove(filename) 
     
    def dispatch(self,event):
        p.apply_async(self.do_process, args = (event, ))
#
    def do_process(self,event):
        
        if event.event_type=="created":
            filename=event.src_path
            try:
                self.decode_pcap(filename)     
            except Exception as e:
                 logger.error("error spotted on  line 30 watcher.py file")
                 logger.error(e)
if __name__ == "__main__":
    
    logger.info("pcap watcher ")
    path = pcapFolderName
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(tempDecodedFolderName):
        os.makedirs(tempDecodedFolderName)   
    # num_workers = mp.cpu_count()
    # processes=num_workers-2
    p = Pool(10)
    watcher = Watcher()
    observer = Observer()
    observer.schedule(watcher, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()