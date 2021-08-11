import time
from time import gmtime, strftime
import urllib.parse
from typing import Optional, Dict, Any, List

from requests import Request, Session, Response
import hmac
import json

class FtxClient:
    _ENDPOINT = 'https://ftx.com/api/'

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    def get_balances(self, coinName: str) -> List[dict]:
        mm = self._get('wallet/balances')
        coin_index = [ x['coin'] for x in mm ].index(coinName)
        coin_balance  = mm[coin_index]['total']
        return coin_balance

    def set_lending_offer(self, coin: str, size: float, rate:float):
        return self._post(f'spot_margin/offers', {'coin': coin,
                                     'size': size,
                                     'rate': rate
                                     })

    def readConfFile(self,fileName):
        count = 0 ;
        confList=[]
        with open("ftxOpt/"+fileName+'.json') as json_file:
            data = json.load(json_file)


second=3600
print("Mio FTX USD放貸複利程式 v0.1")
while True:
    with open('apikey.json', 'r') as json_file:
        api = json.load(json_file)
    mio = FtxClient(api["api-key"], api["api-secret"])
    balanceUSD = mio.get_balances('USD')
    mio.set_lending_offer('USD', balanceUSD, 1e-6)
    if balanceUSD != 0:
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime())+" 已複利")
    else:
        print("USD帳戶餘額為0")
    time.sleep(second)