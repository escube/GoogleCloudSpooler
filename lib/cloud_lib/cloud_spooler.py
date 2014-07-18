#!/usr/bin/python
# _*_ coding: utf-8 -*-

__author__ = "Raffaele Mazzitelli"
__credits__ = ["Raffaele Mazzitelli"]
__maintainer__ = "Raffaele Mazzitelli"
__email__ = "it.escube@gmail.com"
__status__ = "Test"


import base64	#used for base64 encoding of files
import httplib	#provides some high level HTTP services
import json	#provides high level JSON parsing functions
import mimetypes	#provides high level methods for evaluating mime data
import time	#time keeping functions
import urllib	#high level interface for www data using URLs
import urllib2 #adds functionality for complex URL interaction
import mimetools
import logging


CRLF = '\r\n'
BOUNDARY = mimetools.choose_boundary()

class CloudSpooler(object): 

    # The following are used for authentication functions.
    FOLLOWUP_HOST = 'www.google.com/cloudprint'
    FOLLOWUP_URI = 'select%2Fgaiaauth'
    GAIA_HOST = 'accounts.google.com'
    LOGIN_URI = '/accounts/ServiceLoginAuth'
    LOGIN_URL = 'https://www.google.com/accounts/ClientLogin'
    SERVICE = 'cloudprint'

    CLOUDPRINT_URL = 'https://www.google.com/cloudprint'
    CLIENT_NAME = 'cloud_spooler'


    # All of the calls to GetUrl assume you've run something like this:
    #tokens = GetAuthTokens(email, password)

    def __init__(self,email,password,OAUTH):
        self.email=email
        self.password=password
        self.OAUTH =OAUTH
        self.tokens=None
        logging.basicConfig()
        self.logger=logging.getLogger('google_print')



#------------------------------------------START------> LOGIN FUNCTIONS      

    def gaiaLogin(self):
        """Login to gaia using HTTP post to the gaia login page.

        Args:
          email: string,
          password: string
        Returns:
          dictionary of authentication tokens.
        """
        tokens = {}
        cookie_keys = ['SID', 'LSID', 'HSID', 'SSID']
        email = self.email.replace('+', '%2B')
        # Needs to be some random string.
        galx_cookie = base64.b64encode('%s%s' % (email, time.time()))

        # Simulate submitting a gaia login form.
        form = ('ltmpl=login&fpui=1&rm=hide&hl=en-US&alwf=true'
                '&continue=https%%3A%%2F%%2F%s%%2F%s'
                '&followup=https%%3A%%2F%%2F%s%%2F%s'
                '&service=%s&Email=%s&Passwd=%s&GALX=%s' % (self.FOLLOWUP_HOST,
                self.FOLLOWUP_URI, self.FOLLOWUP_HOST, self.FOLLOWUP_URI, self.SERVICE, email,
                self.password, galx_cookie))
                
        login = httplib.HTTPS(self.GAIA_HOST, 443)
        
        login.putrequest('POST', self.LOGIN_URI)
        login.putheader('Host', self.GAIA_HOST)
        login.putheader('content-type', 'application/x-www-form-urlencoded')
        login.putheader('content-length', str(len(form)))
        login.putheader('Cookie', 'GALX=%s' % galx_cookie)
        
        login.endheaders()
        
        
        login.send(form)

        (errcode, errmsg, headers) = login.getreply()
        login_output = login.getfile()
        login_output.close()

       
        login.close()


        for line in str(headers).split('\r\n'):
          if not line: continue
          (name, content) = line.split(':', 1)
          if name.lower() == 'set-cookie':
            for k in cookie_keys:
              if content.strip().startswith(k):
                  tokens[k] = self.getCookie(k, content)

        if not tokens:
          return None
        else:
          return tokens
          
    def refreshAuthTokens(self):
        """Assign login credentials from GAIA accounts service.

        Args:
          email: Email address of the Google account to use.
          password: Cleartext password of the email account.
        Returns:
          dictionary containing Auth token.
        """
        # First get GAIA login credentials using our gaiaLogin method.
        self.tokens = self.gaiaLogin()
       
        # We still need to get the Auth token.
        params = {'accountType': 'GOOGLE',
                  'Email': self.email,
                  'Passwd': self.password,
                  'service': self.SERVICE,
                  'source': self.CLIENT_NAME}
        #print (self.LOGIN_URL, urllib.urlencode(params))       
        stream = urllib.urlopen(self.LOGIN_URL, urllib.urlencode(params))

        for line in stream:
          if line.strip().startswith('Auth='):
            self.tokens['Auth'] = line.strip().replace('Auth=', '')
        
        return self.tokens
#------------------------------------------END------> LOGIN FUNCTIONS      

#------------------------------------------START------> PRINTER FUNCTIONS      

    def getPrinterStatus(self,idPrinter):
      self.refreshAuthTokens()
      
      printers = {}
      values = {}
      tokens_n = ['"id"', '"name"', '"proxy"']
      for t in tokens_n:
        values[t] = ''
      try: 
        response = self.getUrl('%s/printer?printerid=%s&extra_fields=connectionStatus' % (self.CLOUDPRINT_URL,idPrinter),self.tokens)
        
        data = json.loads(response)
        return data['printers'][0]['connectionStatus']
       
      except:
        return "ERROR"

    def getPrinters(self,proxy=None):
      """Get a list of all printers, including name, id, and proxy.

      Args:
        proxy: name of proxy to filter by.
      Returns:
        dictionary, keys = printer id, values = printer name, and proxy.
      """
      self.refreshAuthTokens()
      
      printers = {}
      values = {}
      tokens_n = ['"id"', '"name"', '"proxy"']
      for t in tokens_n:
        values[t] = ''
        
      
      
      if proxy:
        response = self.getUrl('%s/list?proxy=%s' % (self.CLOUDPRINT_URL, proxy),self.tokens)
      else:
        response = self.getUrl('%s/search' % self.CLOUDPRINT_URL,self.tokens)
        
      data = json.loads(response)
      #pprint(data)

      for printer in data['printers']:
        #pprint(printer)
        if printer["id"]:
          printers[printer["id"]] = {}
          printers[printer["id"]]['name'] = printer["name"]
          printers[printer["id"]]['proxy'] = printer["proxy"]
          printers[printer["id"]]['displayName'] = printer["displayName"]
          printers[printer["id"]]['description'] = printer["description"]
          printers[printer["id"]]['id'] = printer["id"]
        

      return printers


    
        
      
#------------------------------------------END------> PRINTER FUNCTIONS      
#------------------------------------------START------> SPOOLER FUNCTIONS      

    def getJobs(self):
        try:
            self.refreshAuthTokens()
            response = self.getUrl('%s/jobs' % (self.CLOUDPRINT_URL, ), self.tokens)
            jobs=json.loads(response)
            ret_dict={}
            for job in jobs['jobs']:
                ret_dict[job['id']]=job

            return ret_dict
        except:
            return None



    def submitPdf(self,printerid, jobsrc):
        
        self.refreshAuthTokens()

        b64file = self.base64Encode(jobsrc)
        content = self.readFile(b64file)
        hsid = True

        title="%s"%jobsrc

        
        content_type = 'dataUrl'

        headers = [('printerid', printerid),
                     ('title', title),
                     ('content', content),
                     ('contentType', content_type)]
          
        files = [('capabilities', 'capabilities', '{"capabilities":[]}')]
        edata = self.encodeMultiPart(headers, files)
        response = self.getUrl('%s/submit' % self.CLOUDPRINT_URL, self.tokens, data=edata, cookies=False)
     
        data = json.loads(response)
      
        ret_data={"success": False,"job":None}
        
        if data['success']:
            ret_data['success']=data['success']
            ret_data['job']=data['job']

        return ret_data


    def submitJob(self,printerid, jobtype, jobsrc):
      """Submit a job to printerid with content of dataUrl.

      Args:
        printerid: string, the printer id to submit the job to.
        jobtype: string, must match the dictionary keys in content and content_type.
        jobsrc: string, points to source for job. Could be a pathname or id string.
      Returns:
        boolean: True = submitted, False = errors.
      """
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

      response = self.getUrl('%s/submit' % self.CLOUDPRINT_URL, self.tokens, data=edata,
                        cookies=False)
      print response
      status = self.validate(response)
      if not status:
        error_msg = self.getMessage(response)
        self.logger.error('Print job %s failed with %s', jobtype, error_msg)

      return status      




#------------------------------------------END------> SPOOLER FUNCTIONS      
#------------------------------------------START------> UTILITY FUNCTIONS      

    def encodeMultiPart(self,fields, files, file_type='application/xml'):
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

    def getUrl(self,url, tokens, data=None, cookies=False, anonymous=False):
      """Get URL, with GET or POST depending data, adds Authorization header.

      Args:
        url: Url to access.
        tokens: dictionary of authentication tokens for specific user.
        data: If a POST request, data to be sent with the request.
        cookies: boolean, True = send authentication tokens in cookie headers.
        anonymous: boolean, True = do not send login credentials.
      Returns:
        String: response to the HTTP request.
      """
      request = urllib2.Request(url)
      if not anonymous:
        if cookies:
          self.logger.debug('Adding authentication credentials to cookie header')
          request.add_header('Cookie', 'SID=%s; HSID=%s; SSID=%s' % (
              tokens['SID'], tokens['HSID'], tokens['SSID']))
        else:  # Don't add Auth headers when using Cookie header with auth tokens.
          request.add_header('Authorization', 'GoogleLogin auth=%s' % tokens['Auth'])
      request.add_header('X-CloudPrint-Proxy', 'api-prober')
      if data:
        request.add_data(data)
        request.add_header('Content-Length', str(len(data)))
        request.add_header('Content-Type', 'multipart/form-data;boundary=%s' % BOUNDARY)

      # In case the gateway is not responding, we'll retry.
      retry_count = 0
      try:
        result = urllib2.urlopen(request).read()
        return result
      except urllib2.HTTPError, e:
        # We see this error if the site goes down. We need to pause and retry.
        err_msg = 'Error accessing %s\n%s' % (url, e)
        self.logger.error(err_msg)
        self.logger.info('Pausing %d seconds', 60)
        return err_msg


    def getCookie(self,cookie_key, cookie_string):
        """Extract the cookie value from a set-cookie string.

        Args:
          cookie_key: string, cookie identifier.
          cookie_string: string, from a set-cookie command.
        Returns:
          string, value of cookie.
        """
        self.logger.debug('Getting cookie from %s', cookie_string)
        id_string = cookie_key + '='
        cookie_crumbs = cookie_string.split(';')
        for c in cookie_crumbs:
          if id_string in c:
            cookie = c.split(id_string)
            return cookie[1]
        return None


    def getMessage(self,response):
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


    def readFile(self,pathname):
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

    def writeFile(self,file_name, data):
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

    def base64Encode(self,pathname):
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
        print "*"*2000
        return None

    def validate(self,response):
      """Determine if JSON response indicated success."""
      if response and response.find('"success": true') > 0:
        return True
      else:
        return False

#------------------------------------------END------> UTILITY FUNCTIONS      

