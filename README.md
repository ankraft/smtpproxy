# smtpproxy

A small SMTP Proxy Server written in Python

**Version**: 1.6.0

*smtpproxy* is a Python script that implements a small SMTP proxy server. It can be used, for example, when the real remote SMTP server requires applications to implement the pop-before-pp authentication scheme and the application doesn't have support for this scheme. An example for this are php-based applications such as the phpBB forum.

The proxy can also be extended by handlers to further process emails send by devices, for example for extracting voice messages received and forwarded by a local PBX. See the [Mail Handler](#mailhandler) section below.


The core of the *smtpproxy* is based on the *smtps.py* script by Les Smithon (original located at [http://www.hare.demon.co.uk/pysmtp.html](http://www.hare.demon.co.uk/pysmtp.html) but the link seems to be dead). Some small modifications to the original implementation were made to make the connection handling multi-threaded. This modified version of the the smtp-script is included in the zip-file.

The server stores received mails temporarily in a sub-directory *msgs*. A separate thread in the script is responsible to send the mails to the configured destination SMTP server, optionally performing the POP-before-SMTP authentication and calling email handlers.

## Changes

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes.


## Installation

#### Prerequisites
- Python 2.6

#### Installation & Configuration
- Clone the repository or download the files to a directory.
- Edit the file smtpproxy.ini (see [Configuration](#configuration) instructions below).

#### Running
- Execute the script smtpproxy.py, eg. enter ``python smtpproxy.py`` on the command line.

The script creates a directory *msgs* for the the temporary files in the same directory as the script (if not specified otherwise in the configuration). The activities (and possible errors) are logged in the log file specified in the configuration file.

#### Install As a Service

Besides of running the *smtpproxy* from a command line the script can be installed as a system service. The script [smtpproxy.init.d](smtpproxy.init.d) can be used to set it for using init.d :

- Copy the script [smtpproxy.init.d](smtpproxy.init.d) to ``/etc/init.d/smtpproxy``
- Set the variable *DAEMON_PATH* in the script to the installation path of *smtpproxy*.
- Start the service, e.g. as root, via the *service* command: ``service smtpproxy start``.

<a href="configuration"></a>
## Configuration

The proxy server is configured by an ini-style configuration file in the current working directory of the server. The name of this file is *smtpproxy.ini*. The file [smtpproxy.ini.example](smtpproxy.ini.example) can be used as a start to setup a configuration file.


The individual sections are explained in the following sections.

### Basic Configuration \[config]

``` ini
[config]
port=25
sleeptime=30
debuglevel=0
waitafterpop=5
deleteonerror=true
```

- **port=&lt;integer>** : This is the port for the local SMTP server. Optional. The default is *25*.
- **sleeptime=&lt;integer>** : The time to wait for the relaying thread to wait between checks for work, in seconds. Optional. The default is *30*.
- **debuglevel=&lt;integer>** : This sets the debuglevel for various functions. The default is *0* (no debug output). See [https://docs.python.org/3/library/smtplib.html#smtp-objects](https://docs.python.org/3/library/smtplib.html#smtp-objects) *SMTP.set_debuglevel* for further information.
- **waitafterpop=&lt;integer>** : The time to wait after a first pop authentication attempt, in seconds. The default is *5*. 
- **deleteonerror=&lt;boolean>** : Delete a mail when an error occurs. The default *true*.


### Logging Configuration \[logging]

``` ini
[logging]
file=smtpproxy.log
size=1000000
count=10
level=INFO
```

- **file=&lt;string>** : Path and name of the log file. Optional. The default is *smtpproxy.log*.  
- **size=&lt;integer>** : Size of the log file before splitting it up into a new logfile. Optional. The default is *1000000*.
- **count=&lt;integer>** : Number of log files to keep. Optional. The default is *10*.  
- **level=&lt;string>** : One of *INFO*, *WARNING*, *ERROR* or *NONE*. In case of *NONE*, only critical errors are logged. Optional. The default is *INFO*.

### Sender's Mail Account Configuration

This section must be configured for each sender's mail account, so it may appear more than once in the configuration file.

Please note, that *smtpproxy* can connect to one or more remote SMTP servers. For each remote server a separate mail account section must be configured.

``` ini
[<mail address of the sender, eg. foo@localdomain.com>]
localhostname=localdomain.com
smtphost=smtp.example.com
smtpsecurity=ssl
smtpusername=username
smtppassword=password
popbeforesmtp=true
pophost=pop.example.com
popport=995
popssl=true
popusername=username
poppassword=password
popcheckdelay=60
returnpath=me@example.com
replyto=me@example.com
```

**General Settings**

- **localhostname=&lt;string>** : The host name used by the proxy to identify the local host to the remote SMTP server. Optional.

**SMTP Settings**

- **smtphost=&lt;string>** : The host name of the receiving SMTP server. Mandatory.
- **smtpport=&lt;integer>** : The port of the receiving SMTP server. Optional. The default is depends on the *smtpsecurity* type (*none* and *tls*: 25, *ssl*: 465).
- **smtpsecurity=&lt;string>** : Indicates the type of the communication security to the SMTP server. Either "tls", "ssl", or "none" (all lowercase, without ".."). The default is "none".
- **smtpusername=&lt;string>** : The username for the SMTP account. Optional, but this entry must be provided if the SMTP server needs authentication.
- **smtppassword=&lt;string>** : The password for the SMTP account. Optional, but this entry must be provided if the SMTP server needs authentication.  
**PLEASE NOTE**: The password is stored in plain text! See also the discussion regarding [Security](#security).

**POP3 Settings**

- **popbeforesmtp=&lt;boolean>** : Indicate whether POP-before-SMTP authentication must be performed. Optional, *true* or *false*. The default is *false*.
- **pophost=&lt;string>** : The host name of the POP3 server. Mandatory only if *popbeforesmtp* is set to *true*.
- **popport=&lt;integer>** : The port of the POP3 server. Optional. The default is *995*. Change this to *110* for non-SSL connections.
- **popssl=&lt;bool>** :Indicates whether the POP connection should be using SSL. The default is true.
- **popusername=&lt;string>** : The username for the POP3 account. Mandatory only if *popbeforesmtp* is set to *true*.
- **poppassword=&lt;string>** : The password for the POP3 account. Mandatory only if *popbeforesmtp* is set to *true*.  
**PLEASE NOTE**: The password is stored in plain text! See also the discussion regarding [Security](#security).
- **popcheckdelay=&lt;integer>** : The time to wait before to re-authenticate again with the POP3 server, in seconds. Optional. The default is *60*.

**Mail Header Fields**

- **returnpath=&lt;string>** : Specifies a bounce email address for a message. Optional.
- **replyto=&lt;string>** : Specifies a reply email address for a message response. Optional.

**Refer to Another Configuration**

Instead of creating a new Sender's Mail Configuration for every account, one can setup an account by just referring to another configuration by using the ``use=`` configuration entry. This must be the only setting for this account.

- **use=&lt;string>** : The name of another account configuration. If this is set then the configuration data of that account is taken instead.

## How to use

After configuring and starting the *smtpserver* the clients need to be configured to use the proxy. For this, usually the following values needs to be set:

- **SMTP Server Host**: This is the address or hostname of the host on which the *smtpserver* runs.
- **SMTP Server Port**: The port number on which the *smtpserver* listens locally for incoming connections. This is the value of the *port* entry in the *[config]* section of the configuration file.
- **e-mail User Name or Account**: The **local** user name. This is the account that was used as a section title to set the sender's mail account configuration, e.g. *foo@localdomain.com* in the example above.

<a href="security"></a>
## Security
### Account Information

Please note, that account information (usernames and passwords) are stored in plain text in the configuration file. You need to make sure that *smtpproxy*'s directory, can only be read and executed by the account under which the *smtpproxy* is run by setting the file permissions accordingly:

	$ chown -R <smtpproxy user>:<smtpproxy group> smtpproxy
	$ chmod 700 smtpproxy

### Local communication
So far, only unencrypted local communication is supported.

### Remote communication
POP3 communication can be secured by using SSL for POP3 (port 995). This is the default.

SMTP communication can be secured by using TLS for SMTP (on the same port), or SMTP over SSL.

<a href="mailhandler"></a>
## Mail Handler Extensions

Before forwarding a received mail, the *smtpproxy* can call handlers to process the mail. This feature can be used, for example, to extract and store voice messages that are forwarded by email from the answering machine of a home router. A handler can also be used to stop further processing / discarding an email.

During startup *smtpproxy* loads all python modules in the sub-directory *handlers*. Each module contains a class that is derived from the abstract class [MailHandler](MailHandler.py) and must implement the following methods:

- **MailHandler.isEnabled()** : Indicates whether a handler is enabled. Returns *True* or *False* respectively.
- **MailHandler.setLogger(logger)** : This method is used to inject the logger instance into the handler. The logger can be used to log results and debug messages from the handler.
- **MailHandler.handleMessage(message, mail, callback)** : This message is called to handle a message. The *message* is an email object that conforms to the Python email library package. *mail* is an internal Mail object with the fields 'Mail.to', 'Mail.frm' and 'Mail.msg'. *callback* is an object with two methods 'setTo(string)' and 'setFrom(string)' to set the respective header fields.  See [https://docs.python.org/2/library/email.html](https://docs.python.org/2/library/email.html) for details.  
This method must return *True* when the email was processed normally. When this methd returns *False*, then no further email processing happens and the currently processed email is discarded (ie. not send).


## License

The *smtpproxy* is available under the MIT license, with the exception of the *smtps.py* script that comes with its own license.

---

The MIT License (MIT)

Copyright (c) 2007 - 2018 Andreas Kraft

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
