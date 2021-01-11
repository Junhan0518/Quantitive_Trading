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
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.average_price = np.array([])
        self.Accum =0
        self.ma_long = 400
        self.ma_short = 100
        self.ma_med=250
        self.UP = 1
        self.DOWN = 2


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    

    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        m_ma = talib.SMA(self.close_price_trace, self.ma_med)[-1]

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']))
       
        
        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []
        
        # if close_price>650 and close_price<660:
        #     Log('buying, opt3: 5')
        #     self.last_type = 'buy'
        #     self.last_cross_status = cur_cross
        #     return [
        #         {
        #             'exchange': exchange,
        #             'amount': 5,
        #             'price': 660,
        #             'type': 'LIMIT',
        #             'pair': pair,
        #         }
        #     ]

        # cross up
        if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            self.Accum =0
            return [
                {
                    'exchange': exchange,
                    'amount': 20,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            self.Accum += 1
            return [
                {
                    'exchange': exchange,
                    'amount': -(self['assets'][exchange]['ETH'])*(3/5),
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        
        #l_ma and s_ma
        elif close_price >l_ma and close_price>s_ma and close_price>m_ma:
            Log('buying, opt1:' + self['opt2'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            self.Accum +=1
            return [
                {
                    'exchange': exchange,
                    'amount': 20,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        elif close_price  < l_ma and close_price < s_ma and close_price<m_ma:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            self.Accum=0
            return [
                {
                    'exchange': exchange,
                    'amount': -10,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        if close_price >= l_ma*1.1:
            Log('buying, opt3: 10')
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            self.Accum +=1
            return [
                {
                    'exchange': exchange,
                    'amount': 30,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif close_price <= l_ma*0.9:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            self.Accum=0
            return [
                {
                    'exchange': exchange,
                    'amount': -(self['assets'][exchange]['ETH']),
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        if (self['assets'][exchange]['USDT']) <= 5000 and close_price <s_ma:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            self.Accum=0
            return [
                {
                    'exchange': exchange,
                    'amount': -10,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]    
            
        
        self.last_cross_status = cur_cross
        return []
