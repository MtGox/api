#!/usr/bin/env python

import mtgox
import json
import os.path

if __name__ == '__main__':
	credentials = {
		'Key': None,
		'Secret': None
	}
	auth = False

	if os.path.exists('../.apirc'):
		with open('../.apirc') as f:
			data = json.loads(f.read())
			if 'Key' in data and 'Secret' in data:
				credentials = data
				auth = True

	# add an error opener
	api = mtgox.api(credentials['Key'], credentials['Secret'])
	print(api.call('2/BTCUSD/money/ticker', auth=False))

	if auth:
		print(api.call('2/money/info'))
