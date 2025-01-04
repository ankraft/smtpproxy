# CHANGELOG

## 1.7.0

04Jan2024

* Thanks to @nebm51 for the following contributions.
* Added support for a "default" account configuration that provides fallback account settings.
* Added a new account configuration setting "from" that adds a missing *from* header in mails.
* Added an option to support weak SSL configuration for outdated SMTP servers.
* Improved Python 3 compatibility.


## 1.6.0

26Sep2018

* Added MailHandler support for discarding emails.
* Fixed wrong MailHandler example.

## 1.5.2

30Dec2017

* Fixed wrong default assignment in remote SMPT port configuration.

## 1.5.1

03Nov2017

* Fixed possible duplicate temporary filename in high-volume scenarios.

## 1.5 

28Oct2017

* Fixed wrong reading of 'popcheckdelay' configuration value.
* Added support for SMTP over SSL.  
**This change replaces the 'smtptls' configuration entry with 'smtpsecurity' and allowed values of 'none', 'tls' and 'ssl'. Also, the default of the 'smtpport' depends on the smtp security type.**

## 1.4

11Dec2016

* Added support for Return-Path: mail header field.
* Added support for changing to: and from: header field in mail handler.

## 1.3 

02Apr2016

* Added TLS and POP3 SSL support.
* Added MailHandler base class

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
