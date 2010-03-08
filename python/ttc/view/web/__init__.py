#! /usr/bin/python
# -*- coding: iso-8859-1; -*-

"""

This package contains classes and functions used to render the web
interface

"""

__all__ = ["jobs"]

import re, time

def EH(html):
    """
    Escapes <, >, & and \" in HTML strings

    Should always be used when outputting any user-originated data to
    HTML (to avoid cross-site scripting attacks etc.)
    """

    return html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

class Page(object):
    """

    Base class for all web interface pages
    
    """
    
    args = None # Help string for web interface
    showDebug = True # Show debug info (performance) if showDebug is True and debug mode is on

    # Used for parsing HTML template files
    reTitle = re.compile(r'<title>(.*?)</title>', re.DOTALL)
    reBody  = re.compile(r'<body>(.*)</body>', re.DOTALL)

    def __init__(self, req):
        """

          * req: req object from mod_python
        
        """
        
        super(Page, self).__init__()

        self.req = req

        self.htmlRoot = self.req.config["path"]["html"]

        self.title = None
        
        self.user = self.GetUser()

    def SendHeader(self, contentType = "text/html; charset=utf-8"):
        """

        Sets content-type and sends HTTP header
        
        """

        self.SetCacheHeaders()

        self.req.content_type = contentType
        self.req.send_http_header()

    def GetUser(self):
        """

        Not yet implemented: Always returns None
        
        """

        return None

    def SetCacheHeaders(self):
        """

        Sets appropriate caching parameters (especially important for
        IE)
        
        """

        # Most pages are dynamic and user-specific and should
        # therefore not be cached
        self.req.headers_out["Cache-Control"] = "no-cache"
        self.req.headers_out["Pragma"] = "no-cache"
        self.req.headers_out["Expires"] = "-1"

    def __call__(self):
        """

        Should normally not be overriden by subclasses

        """
        
        res = self.Main()

        if self.showDebug and self.req.config["debug"]["debugMode"]:
            elapsed = time.time() - self.req.debugThen
            self.Write("\n\n<!-- %f (%i) -->" % (elapsed, 1 / elapsed))

        return res

    def Main(self):
        """

        Override this to provide other functionality
        
        """
        
        self.SendHeader()
        html = self.LoadTemplate()

        self.Write(html)
        return apache.OK

    def Write(self, s):
        """

        Equivalent to self.req.write(s)

        """

        self.req.write(s)

    def ReturnError(self, status, error, suggestion):
        """

        Set HTTP error status and return json-formatted error messages to the client.

        status     : HTTP return codes (RFC 2616)
        error      : string describing error situation
        suggestion : string indicating reason or problem fix
        Returns    : HTTP OK (200) to be transmitted to surrounding layer
        Used by    : http-handlers in view.web.jobs

        """

        self.SendHeader("application/json")
        self.req.status = status  # Must set status before calling write !
        self.Write("{\n  \"Error\" : \"%s\",\n  \"Suggestion\" : \"%s\"\n}\n" % (error, suggestion))
        return apache.OK

