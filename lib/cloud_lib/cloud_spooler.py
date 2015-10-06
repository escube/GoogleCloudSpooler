#!/usr/bin/python
# _*_ coding: utf-8 -*-


import base64  # used for base64 encoding of files
import ConfigParser  # parses plain text config files
from httplib2 import Http
import httplib2
import json  # provides high level JSON parsing functions
import mimetypes  # provides high level methods for evaluating mime data
import optparse  # parses incoming command line arguments
import os  # OS level functions and interaction
import string  # high level string functions
import sys  # high level system functions
import time  # time keeping functions
import urllib  # high level interface for www data using URLs
import mimetools
import logging
from pprint import pprint

from oauth2client.client import SignedJwtAssertionCredentials

CRLF = '\r\n'
BOUNDARY = mimetools.choose_boundary()


class CloudSpooler(object):

    CLOUDPRINT_URL = 'https://www.google.com/cloudprint'

    def __init__(self, client_email, private_key):
        self.client_email = client_email
        self.private_key = private_key
        scope = 'https://www.googleapis.com/auth/cloudprint'
        httplib2.debuglevel=0
        self.credentials = SignedJwtAssertionCredentials(client_email, private_key, scope=scope)

        self.http_auth = self.credentials.authorize(Http())

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('google_print')


    def refresh(self):
	self.credentials.refresh(self.http_auth)


    # ------------------------------------------START------> PRINTER FUNCTIONS

    def getPrinterStatus(self, idPrinter):
	self.refresh()
        printers = {}
        values = {}
        tokens_n = ['"id"', '"name"', '"proxy"']
        for t in tokens_n:
            values[t] = ''
        try:

            (resp_headers, response) = self.http_auth.request(
                '%s/printer?printerid=%s&extra_fields=connectionStatus' % (self.CLOUDPRINT_URL, idPrinter), method="GET")

            data = json.loads(response)
            return data['printers'][0]['connectionStatus']

        except:
            return "SERVICE NOT WOKING -- ERROR"

    def getPrinters(self, proxy=None):
        """Get a list of all printers, including name, id, and proxy.

        Args:
          proxy: name of proxy to filter by.
        Returns:
          dictionary, keys = printer id, values = printer name, and proxy.
        """
	self.refresh()

        printers = {}
        values = {}
        tokens_n = ['"id"', '"name"', '"proxy"']
        for t in tokens_n:
            values[t] = ''

        (resp_headers, content) = self.http_auth.request('%s/search' % self.CLOUDPRINT_URL, method="GET")

        data = json.loads(content)
        pprint(data)

        for printer in data['printers']:
            # pprint(printer)
            if printer["id"]:
                printers[printer["id"]] = {}
                printers[printer["id"]]['name'] = printer["name"]
                printers[printer["id"]]['proxy'] = printer["proxy"]
                printers[printer["id"]]['displayName'] = printer["displayName"]
                printers[printer["id"]]['description'] = printer["description"]
                printers[printer["id"]]['id'] = printer["id"]

        return printers

    def choosePrinter(self, proxy=None):
        """Ti permette di scegleire la stampante sulla quale stampare

        Args:
          proxy: name of proxy to filter by.
        Returns:
          object, keys = id, name, proxy,displayName,description
        """
	self.refresh()
        printers = {}
        values = {}
        tokens_n = ['"id"', '"name"', '"proxy"']
        for t in tokens_n:
            values[t] = ''

        (resp_headers, content) = self.http_auth.request('%s/search' % self.CLOUDPRINT_URL, method="GET")

        data = json.loads(content)

        numero = 0

        print "Stampanti disponibili\n\n"

        for printer in data['printers']:
            if printer["id"]:
                numero += 1
                printers[numero] = {}
                printers[numero]['id'] = printer["id"]
                printers[numero]['name'] = printer["name"]
                printers[numero]['proxy'] = printer["proxy"]
                printers[numero]['displayName'] = printer["displayName"]
                printers[numero]['description'] = printer["description"]

                print "%d : %s" % (numero, printer["name"])

        try:
            input = "\nScegli una stampante da utilizzare selezionando i numero a fianco della stampante e premere invio : "
            scelta = int(raw_input(input))
            # print "hai scelto %d"%(mode,)
            return printers[scelta]

        except ValueError:
            print "\n\n" + "*" * 40 + "ERRORE" + "*" * 40
            print "La tua scelta non è valida, devi scegliere un numero "
            print "*" * 86 + "\n\n"

            return None


            # ------------------------------------------END------> PRINTER FUNCTIONS
            # ------------------------------------------START------> SPOOLER FUNCTIONS

    def getJobs(self):
	self.refresh()
        try:
            (resp_headers, response) = self.http_auth.request('%s/jobs' % (self.CLOUDPRINT_URL,), method="GET")

            jobs = json.loads(response)
            ret_dict = {}
            for job in jobs['jobs']:
                ret_dict[job['id']] = job

            return ret_dict
        except:
            return None


    def submitPdf(self, printerid, jobsrc):
	self.refresh()
    
        b64file = self.base64Encode(jobsrc)
        content = self.readFile(b64file)
        hsid = True
    
        title = "%s" % jobsrc
    
        content_type = 'dataUrl'
    
        headers = [('printerid', printerid),
                   ('title', title),
                   ('content', content),
                   ('contentType', content_type)]
    
        files = [('capabilities', 'capabilities', '{"capabilities":[]}')]
        edata = self.encodeMultiPart(headers, files)
        headers=[('Content-Length', str(len(edata))),('Content-Type', 'multipart/form-data;boundary=%s' % BOUNDARY)]


        (resp_headers, response) = self.http_auth.request('%s/submit' % (self.CLOUDPRINT_URL,),method='POST', headers=headers,
                                                          body=edata)

        data = json.loads(response)
    
        ret_data = {"success": False, "job": None}
    
        if data['success']:
            ret_data['success'] = data['success']
            ret_data['job'] = data['job']
    
        return ret_data


    def submitJob(self, printerid, jobtype, jobsrc):
        """Submit a job to printerid with content of dataUrl.

        Args:
          printerid: string, the printer id to submit the job to.
          jobtype: string, must match the dictionary keys in content and content_type.
          jobsrc: string, points to source for job. Could be a pathname or id string.
        Returns:
          boolean: True = submitted, False = errors.
        """
	self.refresh()
        if jobtype == 'pdf':
            b64file = self.base64Encode(jobsrc)
            fdata = self.readFile(b64file)
            hsid = True
        elif jobtype in ['png', 'jpeg']:
            fdata = self.readFile(jobsrc)
        else:
            fdata = None

        # Make the title unique for each job, since the printer by default will name
        # the print job file the same as the title.

        title = '%s' % (jobsrc,)

        """The following dictionaries expect a certain kind of data in jobsrc, depending on jobtype:
          jobtype                jobsrc
          ================================================
          pdf                    pathname to the pdf file
          png                    pathname to the png file
          jpeg                   pathname to the jpeg file
          ================================================
          """
        content = {'pdf': fdata,
                   'jpeg': jobsrc,
                   'png': jobsrc,
                   }
        content_type = {'pdf': 'dataUrl',
                        'jpeg': 'image/jpeg',
                        'png': 'image/png',
                        }
        headers = [('printerid', printerid),
                   ('title', title),
                   ('content', content[jobtype]),
                   ('contentType', content_type[jobtype])]

        files = [('capabilities', 'capabilities', '{"capabilities":[]}')]
        edata = self.encodeMultiPart(headers, files)
        #print "#"*100
        #print edata
        #print "#"*100


        headers=[('Content-Length', str(len(edata))),('Content-Type', 'multipart/form-data;boundary=%s' % BOUNDARY)]


        (resp_headers, response) = self.http_auth.request('%s/submit' % (self.CLOUDPRINT_URL,),method='POST', headers=headers,
                                                          body=edata)
        #print "*"*100
        #print response
        #print resp_headers
        #print "*"*100

        status = self.validate(response)
        if not status:
            error_msg = self.getMessage(response)
            self.logger.error('Print job %s failed with %s', jobtype, error_msg)

        return status

    # ------------------------------------------END------> SPOOLER FUNCTIONS
    # ------------------------------------------START------> UTILITY FUNCTIONS

    def encodeMultiPart(self, fields, files, file_type='application/xml'):
        """Encodes list of parameters and files for HTTP multipart format.

        Args:
          fields: list of tuples containing name and value of parameters.
          files: list of tuples containing param name, filename, and file contents.
          file_type: string if file type different than application/xml.
        Returns:
          A string to be sent as data for the HTTP post request.
        """
        lines = []
        for (key, value) in fields:
            lines.append('--' + BOUNDARY)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')  # blank line
            lines.append(value)
        for (key, filename, value) in files:
            lines.append('--' + BOUNDARY)
            lines.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"'
                % (key, filename))
            lines.append('Content-Type: %s' % file_type)
            lines.append('')  # blank line
            lines.append(value)
        lines.append('--' + BOUNDARY + '--')
        lines.append('')  # blank line
        return CRLF.join(lines)



    def getMessage(self, response):
        """Extract the API message from a Cloud Print API json response.

        Args:
          response: json response from API request.
        Returns:
          string: message content in json response.
        """
        lines = response.split('\n')
        for line in lines:
            if '"message":' in line:
                msg = line.split(':')
                return msg[1]

        return None


    def readFile(self, pathname):
        """Read contents of a file and return content.

        Args:
          pathname: string, (path)name of file.
        Returns:
          string: contents of file.
        """
        try:
            f = open(pathname, 'rb')
            try:
                s = f.read()
            except IOError, e:
                self.logger('Error reading %s\n%s', pathname, e)
            finally:
                f.close()
                return s
        except IOError, e:
            self.logger.error('Error opening %s\n%s', pathname, e)
            return None

    def writeFile(self, file_name, data):
        """Write contents of data to a file_name.

        Args:
          file_name: string, (path)name of file.
          data: string, contents to write to file.
        Returns:
          boolean: True = success, False = errors.
        """
        status = True

        try:
            f = open(file_name, 'wb')
            try:
                f.write(data)
            except IOError, e:
                self.logger.error('Error writing %s\n%s', file_name, e)
                status = False
            finally:
                f.close()
        except IOError, e:
            self.logger.error('Error opening %s\n%s', file_name, e)
            status = False

        return status

    def base64Encode(self, pathname):
        """Convert a file to a base64 encoded file.

        Args:
          pathname: path name of file to base64 encode..
        Returns:
          string, name of base64 encoded file.
        For more info on data urls, see:
          http://en.wikipedia.org/wiki/Data_URI_scheme
        """
        b64_pathname = pathname + '.b64'
        file_type = mimetypes.guess_type(pathname)[0] or 'application/octet-stream'
        data = self.readFile(pathname)

        # Convert binary data to base64 encoded data.
        header = 'data:%s;base64,' % file_type
        b64data = header + base64.b64encode(data)

        if self.writeFile(b64_pathname, b64data):
            return b64_pathname
        else:
            print "*" * 2000
            return None

    def validate(self, response):
        """Determine if JSON response indicated success."""
        if response and response.find('"success": true') > 0:
            return True
        else:
            return False

# ------------------------------------------END------> UTILITY FUNCTIONS
