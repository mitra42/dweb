from sys import version as python_version
import requests             # For outgoing HTTP http://docs.python-requests.org/en/master/
from Transport import Transport, TransportURLNotFound
from Errors import ToBeImplementedException
import urllib

class TransportHTTPBase(Transport):
    """
    Common parts for TransportHTTP and TransportDist
    """

    def __init__(self, options={}, verbose=False):
        """
        Base class for both TransportHTTP and TransportDist_Peer

        :param blah:
        """
        self.options = options
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
                                    verbose=verbose, data=TransportHTTP.dumps(data), params=options)
        else:
            res = self._sendGetPost(False, "info", urlargs=[], verbose=verbose, params=options)
        return res.json()

