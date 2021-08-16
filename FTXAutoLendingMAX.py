import time
from time import gmtime, strftime, localtime
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
        return self._post('spot_margin/offers', {'coin': coin,
                                     'size': size,
                                     'rate': rate
                                     })

    def get_lening_history(self) -> List[dict]:
        return self._get('spot_margin/lending_history')

    def get_lending_rates(self, coinName: str) -> List[dict]:
        mm = self._get('spot_margin/lending_rates')
        coin_index = [ x['coin'] for x in mm ].index(coinName)
        estimate  = mm[coin_index]['estimate']
        return estimate


second=3600
print("--------------------------------------------------------------------")
print("FTX放貸複利程式 v0.4")
print("")
print("程式作者: Mio Su<mioxtw@gmail.com>")
print("")
print("使用方法：")
print("請修改apikey.json，填入你的API_KEY和API_SECRET")
print("enableUSD是開啟複利USD，預設是true，關閉請改成false，以此類推")
print("minRateUSD是最小時利率，預設是0.000001")
print("--------------------------------------------------------------------")
print("")
print("如果本程式對你有幫助，行有餘力請Donate窮苦的碼農程式員，感謝大爺賞賜")
print("")
print("-------我的錢包位址在此---------------------------------------------")
print("USDT(TRC-20): TWx22d9XmMtMeb6mEg48n5C3kwS31iicDf")
print("USDT(ERC-20): 0x10C85D6AE5266E2Af2cFAA688B5348c4c7119062")
print("ETH: 0x10C85D6AE5266E2Af2cFAA688B5348c4c7119062")
print("BTC: 3BYVUVfZJTUXWGKsjjucWKdScKTSJRw8Ck")
print("--------------------------------------------------------------------")
print("")
print("")
while True:
    with open('apikey.json', 'r') as json_file:
        data = json.load(json_file)

    enableUSD = data["enableUSD"]
    enableUSDT = data["enableUSDT"]
    minRateUSD = data["minRateUSD"]
    minRateUSDT = data["minRateUSDT"]

    mio = FtxClient(data["api-key"], data["api-secret"])
    balanceUSD = mio.get_balances('USD')
    balanceUSDT = mio.get_balances('USDT')
    lendingRateUSD = mio.get_lending_rates('USD')
    lendingRateUSDT = mio.get_lending_rates('USDT')
    
    if balanceUSD >= 1 and enableUSD == True:
        mio.set_lending_offer('USD', balanceUSD, minRateUSD)
        print(strftime("%Y-%m-%d %H:%M:%S", localtime())+" 已更新USD 貸款數額：",balanceUSD, "USD ", "下一次預估貸款利率：",lendingRateUSD*24*365*100,"%")
    else:
        if enableUSD == True:
            print("USD帳戶餘額少於 1 USD，無法放貸")

    if balanceUSDT >= 1 and enableUSDT == True:
        mio.set_lending_offer('USDT', balanceUSDT, minRateUSDT)
        print(strftime("%Y-%m-%d %H:%M:%S", localtime())+" 已更新USDT貸款數額：",balanceUSDT, "USDT ", "下一次預估貸款利率：",lendingRateUSDT*24*365*100,"%")
    else:
        if enableUSDT == True:
            print("USDT帳戶餘額少於 1 USDT，無法放貸")

    time.sleep(second)
