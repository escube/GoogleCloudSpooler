This project implement a simple library and a standalone program that allows to print using the service Google Cloud Print.
More informations are found on http://www.google.com/cloudprint/learn/.

Please note some of the code in the library is taken from other source on the Internet.

To use this library you need the following :
1) Email from Google
2) Password
3) OAUTH from google. (more information on this https://developers.google.com/accounts/docs/OAuth2)
4) A computer that is connected to the printer you want to use with this service. 
Please note it's all very flexible and how you connect the printer with Google Cloud Printer doesn't influence the use of this library.
I used a windows machine with Chrome on it, and added printers to Chrome

With these informations you can fill in the file conf.json and use it as you need.
{
    "email": "mymail@gmail.com",
    "password": "mymailpassword",
    "OAUTH": "myOAUTH",
    "printer":null
}

The "printer" in this file is optional, and indicate the name of the printer to use. 
If no printer is provided you will have the possibility to choose from the ones available on your Google Cloud Printer Manager.

Play and use this library as you wish.
If you have suggestions or want to contribute send me an email.

