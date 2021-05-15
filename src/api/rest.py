import requests
from requests.packages.urllib3.util.retry import Retry
requests.packages.urllib3.disable_warnings()


class RestClient(object):
    def __init__(self, retry_count=5):
        self.session = requests.Session()
        retries = Retry(total=retry_count, backoff_factor=0.2,
                        status_forcelist=[500, 502, 503, 504, 400, 408])
        retry = requests.adapters.HTTPAdapter(max_retries=retries)
        self.session.mount('https://', retry)
        self.cert = None
        self.verify = False

    def get(self, **kwargs):
        return self.session.get(kwargs['url'], headers=kwargs['headers'], cert=self.cert, verify=self.verify)

    def patch(self, **kwargs):
        return self.session.patch(kwargs['url'], data=kwargs['data'], headers=kwargs['headers'],
                                  cert=self.cert, verify=self.verify)

    def post(self, **kwargs):
        return self.session.post(kwargs['url'], data=kwargs['data'], headers=kwargs['headers'],
                                 cert=self.cert, verify=self.verify)

    def delete(self, **kwargs):
        return self.session.delete(kwargs['url'], headers=kwargs['headers'],
                                   cert=self.cert, verify=self.verify)

    def put(self, **kwargs):
        if 'data' not in kwargs.keys():
            return self.session.put(kwargs['url'], headers=kwargs['headers'],
                                    cert=self.cert, verify=self.verify)
        else:
            return self.session.put(kwargs['url'], data=kwargs['data'], headers=kwargs['headers'],
                                    cert=self.cert, verify=self.verify)