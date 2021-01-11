# Class name must be Strategy
class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 10* 60 #10分鐘線
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.last_kdj_cross = None
        self.obv_trace  = np.array([])
        self.close_price_trace = np.array([])
        self.high_price_trace = np.array([])
        self.low_price_trace = np.array([])
        self.volume_trace = np.array([])
        self.buy_price = np.array([])
        self.buy_frequency = 0.1
    
    def get_current_kdj_cross(self):
        indicators={}
        indicators['K'], indicators['D'] = talib.STOCH(self.high_price_trace,
                                    self.low_price_trace,
                                    self.close_price_trace,
                                    fastk_period=9,
                                    slowk_period=3,
                                    slowk_matype=0,
                                    slowd_period=3,
                                    slowd_matype=0)

        K = indicators.get('K')
        D = indicators.get("D")
        if np.isnan(K[-1]) or np.isnan(D[-1]):
            return None,None,None, None

        indicators['J'] = indicators['K'] * 3 - indicators['D'] * 2
        J = indicators.get("J")
            
        if indicators['K'][-1] > indicators['D'][-1]:
            KDJ_status = 'Up'
        else:
            KDJ_status = 'Down'

        return K,D,J, KDJ_status


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        volume = information['candles'][exchange][pair][0]['volume']
        high = information['candles'][exchange][pair][0]['high']
        low = information['candles'][exchange][pair][0]['low']
        targetCurrency = pair.split('-')[0]  #BTC
        baseCurrency = pair.split('-')[1]  #USDT
  
        baseCurrency_amount = self['assets'][exchange][baseCurrency] 
        targetCurrency_amount = self['assets'][exchange][targetCurrency]

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        self.volume_trace = np.append(self.volume_trace, [float(volume)])
        self.high_price_trace = np.append(self.high_price_trace, [float(high)])
        self.low_price_trace = np.append(self.low_price_trace, [float(low)])
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        K , D, J , KDJ_Cross = self.get_current_kdj_cross()

        # Log('K:' + str(K[-1]) + ' , D : ' + str(D[-1]) + ', J : '+str(J[-1]) + ', Cross : ' + str(KDJ_Cross))

        if K is None:
            return []
        
        if self.last_kdj_cross is None:
            self.last_kdj_cross = KDJ_Cross
            return []

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        rsi = talib.RSI(self.close_price_trace , 6)[-1]
        rsi2 = talib.RSI(self.close_price_trace, 12)[-1]

        if self.buy_frequency >0.8:
            self.buy_frequency = 0.8

        # cross 
        if self.last_type == 'sell':
            amount = baseCurrency_amount * 0.2 / float(close_price)
            self.buy_price = np.append(self.buy_price, [float(close_price)])
            self.last_type = 'buy'
            return [
                    {
                        'exchange': exchange,
                        'amount': amount,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]

        if  (K[-1] < D[-1]) and rsi < rsi2 and volume > np.mean(self.volume_trace[-10:]) * 1.2:
            if rsi <20 or J[-1] <10:
                Log(str(J[-1])+","+str(rsi)+","+str(volume)+","+str(np.mean(self.volume_trace[-10:])))
                if  self.buy_price.size == 0:
                     amount = 0.05
                     self.buy_price = np.append(self.buy_price, [float(close_price)])
                elif  self.last_type =='buy'  and float(close_price)  <= self.buy_price[- 1] * 0.99:
                     amount = baseCurrency_amount/float(close_price) * self.buy_frequency
                     self.buy_price = np.append(self.buy_price, [float(close_price)])
                     self.buy_frequency += 0.1
                elif  float(close_price)  <= self.buy_price[- 1]:
                     amount = 0.05
                else:
                    amount = 0.02
                Log('buying, opt1:' + self['opt1'] + 'money：' + str(baseCurrency_amount))
                self.last_type = 'buy'
                self.last_cross_status = cur_cross
                self.last_kdj_cross = KDJ_Cross
                return [
                    {
                        'exchange': exchange,
                        'amount': amount,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]

        # cross down
        elif  self['assets'][exchange]['BTC'] >0 and  (K[-1] > D[-1]) and rsi > rsi2 and volume > np.mean(self.volume_trace[-10:]) * 2  and float(close_price)  > np.mean(self.buy_price) * 1.3:
            if rsi > 80:
                Log('selling, ' + exchange + ':' + pair)
                self.last_type = 'sell'
                self.last_cross_status = cur_cross
                self.last_kdj_cross = KDJ_Cross
                self.buy_price = np.array([])
                self.buy_frequency = 0.1
                return [
                    {
                        'exchange': exchange,
                        'amount': -1 * targetCurrency_amount,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
        elif  self['assets'][exchange]['BTC'] >0 and float(close_price) > np.max(self.buy_price) * 1.3:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            self.last_kdj_cross = KDJ_Cross
            self.buy_price = np.array([])
            self.buy_frequency = 0.1
            return [
                {
                    'exchange': exchange,
                    'amount': -1 * targetCurrency_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            
        self.last_cross_status = cur_cross
        self.last_kdj_cross = KDJ_Cross
        return []
