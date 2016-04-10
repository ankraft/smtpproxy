# CHANGELOG

## 1.3 
10Apr2016
* Added TLS and POP3 SSL support.
* Added MailHandler base class
* Added *use* configuration option
* Added *deleteonerror* configuration option

## 1.2
10Dec2014
* Added DEBUG to logging
* Fixed wrong return code in AUTH LOGIN
* Added EHLO command in smtp server module
* Added first primitive handling of AUTH LOGIN procedure. Just accept everything for authentication for now.
* Added printing of filename for messagings with missing configuration
* Added mail handlers. Handlers are Python classes that are loaded from a directory and called for each message
* Added log output for authentication

## 1.1
31Mar07
* Added waitforpop, localhostname, and debulgevel configuration options
* Added optional authentication with SMTP servers.

## 1.0
31Jan07
* First Release
