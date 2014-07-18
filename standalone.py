#! /usr/bin/python
__author__ = "Raffaele Mazzitelli"
__credits__ = ["Raffaele Mazzitelli"]
__maintainer__ = "Raffaele Mazzitelli"
__email__ = "it.escube@gmail.com"
__status__ = "Test"

from lib.cloud_lib.cloud_spooler import CloudSpooler
from pprint import pprint
import sys
import json
import readline
import os
import magic
import time





def get_params(argv):
    if(len(argv)<2):
        print "You must specify the configuration file"
        print "usage:"
        print "%s /path/to/conf_file"%argv[0]
        exit(1)
    else:
        try:
            conf_file=argv[1]
            print "loading conf file %s ..."%conf_file
            params=json.load(open(conf_file))
            params["conf_file"]=conf_file
            return params

        except:
            print "your conf file : %s"
            print "is not valid json or doesn't exist"
            exit(1)

def getFileToPrint():
    readline.parse_and_bind('tab: complete')
    while True:
        line = raw_input('File to Print: ')
        if os.path.isfile(line):
            mime_type=magic.from_file(line,mime=True)
            print mime_type
            if mime_type == 'application/pdf' :
                return line
            else:
                print "only pdf file are accepted"
        else:
            print "%s is not a file, please choose a valid file" % line
            
def choosePrinter(cloudSpooler):
    
    printers=cloudSpooler.getPrinters()

    possible_choise=[]
    
    
    for printer in printers:
        possible_choise.append(printers[printer])

    print "\nAvailable printer : "
       
    for i in range(len(possible_choise)):
        display_name=possible_choise[i]['displayName'].lower()
        print "%d) %s"%(i,display_name)
    print ""


    while True:
        line = raw_input('Choose a number from the list above : ')
        if line.isdigit():
            selected=int(line)
            if selected in range(len(possible_choise)):
                return possible_choise[selected]
            else:
                last=len(possible_choise)-1
                print "please select a valid number between 0 and %d"%last
        else:
            print "please select a number"

                
        
def getPrinter(cloudSpooler,printer_in):
    
    printers=cloudSpooler.getPrinters()

    if printer_in:
        printer_in=printer_in.lower()

        for printer in printers:
            display_name=printers[printer]['displayName'].lower()
            if printer_in == display_name:
                #found
                return printers[printer]
    
        print "The printer you in your conf file '%s' is not available on google cloud print"%printer_in
        
    
    return choosePrinter(cloudSpooler)
                
def checkSpooler(cloudSpooler,job_id=None):
    alljobs=cloudSpooler.getJobs()
    #pprint(alljobs)
    if job_id in alljobs.keys():
        statej=alljobs[job_id]['uiState']['summary']
        file_name=alljobs[job_id]['title'].split("/")[-1]
        createTime=int(alljobs[job_id]['createTime'])/1000
        createTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(createTime))
        return {'file':file_name,'state':statej,'time':createTime}
    
    print "File non present in spooler status"
    return None

   
def main(argv) :
   
        params=get_params(argv)
        cloudSpooler=CloudSpooler(params["email"],params["password"],params["OAUTH"])
        
       
        
        while True:
            printer=getPrinter(cloudSpooler,params['printer'])
            
            printer_name=printer['displayName']
            printer_id=printer['id']
            print "checking status of printer %s"%printer_name
            status=cloudSpooler.getPrinterStatus(printer_id)
            print status
            if status != "ONLINE":
                print "the printer you choosed is not ONLINE, please choose another printer"
            else:
                file_to_print=getFileToPrint()
                print "Printing %s ..." %file_to_print
                
                job=None
                job=cloudSpooler.submitPdf(printer_id,file_to_print)
                job_id=job['job']['id']
                if job and job['success']:
                    print "your file has been correctly been updated, checking status ..."
                    while True:
                        status=checkSpooler(cloudSpooler,job_id)
                        if status:
                            print "%s %s %s"%(status['time'],status['file'],status['state'])
                            if status['state']=="DONE":
                                exit(0);
                        #sleep 10 seconds
                        time.sleep(10)
                else:
                    print "sorry was not possble to upload your file for printing"
        
        
      
       
        
if __name__ == '__main__' :
    sys.exit(main(sys.argv))