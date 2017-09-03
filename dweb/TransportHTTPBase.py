from sys import version as python_version
import requests             # For outgoing HTTP http://docs.python-requests.org/en/master/
from Transport import Transport, TransportURLNotFound
from misc import ToBeImplementedException
from CryptoLib import CryptoLib
import urllib

#TODO-BACKPORT - review this file

class TransportHTTPBase(Transport):
    """
    Common parts for TransportHTTP and TransportDist
    """

    def __init__(self, options={}, verbose=False): #TODO-BACKPORT Find callers
        """
        Base class for both TransportHTTP and TransportDist_Peer

        :param blah:
        """
        self.ipandport = options["http"]["ipandport"]
        self.verbose = verbose
        self.baseurl = "http://%s:%s/" % (self.ipandport[0], self.ipandport[1])  # Note trailing /

    def _sendGetPost(self, post, command, urlargs=None, verbose=False, **options):
        """
        Construct a URL of form  baseurl / command / urlargs ? options

        :param post: True if should POST, else GET
        :param command: command passing to server
        :param urlargs: contactenated to command in order given
        :param verbose: if want to display IRL used, place IN params to send to server
        :param params:  passed to requests.get, forms arguments after "?"
        :param headers: passe to requests.get, sent as HTTP headers
        :param options:
        :return: Response - can access via .text, .content and .headers
        """
        url = self.baseurl + command
        if urlargs:
            url += "/" + "/".join(urllib.quote(u) for u in urlargs)
        if verbose: print "sending", "POST" if post else "GET", "request to", url, options
        try:
            r = None
            r = requests.post(url, **options) if post else requests.get(url, **options)
            r.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            if r is not None and (r.status_code == 404):
                raise TransportURLNotFound(url=url, options=options)
            else:
                # print e.__class__.__name__, e
                # TODO-LOGGING: logger.error(e)
                raise e  # For now just raise it
        # print r.status_code, r.text # r.json()
        return r  # r is a response

    def info(self, verbose=False, data=None, **options):
        """
        ERR: ConnectionError (HTTPConnectionPool) if cant reach destn

        :param verbose:
        :param options:
        :return:
        """
        if verbose: print "%s.info" % self.__class__.__name__
        if data:
            res = self._sendGetPost(True, "info", urlargs=[], headers={"Content-Type": "application/json"},
                                    verbose=verbose, data=CryptoLib.dumps(data), params=options)
        else:
            res = self._sendGetPost(False, "info", urlargs=[], verbose=verbose, params=options)
        return res.json()

    def url(self, obj, command=None, url=None, table=None, contenttype=None, url_output=None, **options):
        """

        :return: HTTP style URL to access this resource - not sure what this works on yet.
        """
        # Identical code in TransportHTTP and ServerHTTP.url
        url = url or obj._url
        if command in ["file"]:
            if url_output == "getpost":
                return [False, command, [table or obj.table, url]]
            else:
                res = "http://%s:%s/%s/%s/%s" \
                      % (self.ipandport[0], self.ipandport[1], command, table or obj.table, url)
        else:
            if url_output == "getpost":
                raise ToBeImplementedException(
                    name="TransportHTTP.url:command=" + (command or "None") + ",url_output=" + url_output)
            else:
                res = "http://%s:%s/%s/%s" \
                      % (self.ipandport[0], self.ipandport[1], command or "rawfetch", url)
        if contenttype:
            if command in ("update",):  # Some commands allow type as URL parameter
                res += "/" + urllib.quote(contenttype, safe='')
            else:
                res += "?contenttype=" + urllib.quote(contenttype, safe='')
        return res
