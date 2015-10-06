This project implement a simple library and a standalone program that allows to print using the service Google Cloud Print.
More informations are found on [google](http://www.google.com/cloudprint/learn/.)

Please note some of the code in the library is taken from other source on the Internet.

![here](https://github.com/escube/GoogleCloudSpooler/blob/master/img/cloudprint.png)


To use this library you need the following :

1. User account from google
2. Group from google. You can create one from [here](https://groups.google.com) 
3. [OAUTH from google.](more information on this https://developers.google.com/accounts/docs/OAuth2)
4. Google Chrome

How to proceede : 

1. Create a google account
2. Create a group on google
3. Create in [Google Developers](https://console.developers.google.com) under credentials a new user credential
4. Add the new created service in point 3 to the groupcreated in point 2
5. Connect with credential of you google account of point 1 with google Chrome and following this [guide](https://developers.google.com/cloud-print/docs/overview) add the printers you want to use remotely

Everything should be in place to start.  

With these informations you can fill in the file conf.json and use it as you need.
```
{
    "email": "mymail@gmail.com",
    "password": "mymailpassword",
    "OAUTH": "myOAUTH",
    "printer":null
}
```

The "printer" in this file is optional, and indicate the name of the printer to use. 
If no printer is provided you will have the possibility to choose from the ones available on your Google Cloud Printer Manager.


Play and use this library as you wish.
If you have suggestions or want to contribute send me an email.
