#!/usr/bin/env python

import mtgox

if __name__ == '__main__':
	# add an error opener
	api = mtgox.api()
	print(api.call('2/BTCUSD/money/ticker'))