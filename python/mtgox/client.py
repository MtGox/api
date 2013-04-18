
import mtgox
import datetime
import sys
# used to generate auth secret data
import base64
import hashlib
import hmac
# for parsing the result
import json
# used to run the query and build the URI
if sys.version_info[0] < 3:
	import urllib
	import urllib2
	import urlparse
else:
	import urllib.request
	import urllib.parse
	import urllib.error

# Used when I need to debug the module
#import http.client
#http.client.HTTPConnection.debuglevel = 1

# create a map of functions based on the current python version
if sys.version_info[0] < 3:
	function_map = {
		'create_request': urllib2.Request,
		'urlunsplit': urlparse.urlunsplit,
		'urlencode': urllib.urlencode,
		'urlopen': urllib2.urlopen
	}
	URLError = urllib2.URLError
else:
	function_map = {
		'create_request': urllib.request.Request,
		'urlunsplit': urllib.parse.urlunsplit,
		'urlencode': urllib.parse.urlencode,
		'urlopen': urllib.request.urlopen
	}
	URLError = urllib.error.URLError

"""This function runs one of the function defined in our function map"""
def function_map_run(func, *args):
	return function_map[func](*args)

class api:
	"""
	Small class for calling the MtGox API.

	This class implements authenticated and non-authenticated calls for
	all versions (0, 1 and 2) of the API.

	Right now it doesn't provide any mapping to the MtGox API, though it
	should come in next version, right now basic usage would be something
	like:

		>>> import mtgox
		>>> mtgox_api = mtgox.api("key", "secret")
		>>> my_data = mtgox_api.call("2/money/info")

	Refer to the call method documentation for more details on how to control
	the way the API is called.
	"""
	_default_auth = '_auth_basic'
	_versions = {
		0: '_auth_basic',
		1: '_auth_basic',
		2: '_auth_extended'
	}

	def __init__(self, api_key=None, api_secret=None):
		self.api_key = api_key
		self.api_secret = api_secret

	# The basic auth is used on version 0 and 1 of the API
	def _auth_basic(self, request, path, query):
		# add some headers
		request.add_header('Rest-Key', self.api_key)
		# generate new hmac data
		binary_secret = base64.b64decode(self.api_secret)
		binary_signature = hmac.new(binary_secret, query, hashlib.sha512).digest()
		signature = base64.b64encode(binary_signature)
		# then add it to the headers
		request.add_header('Rest-Sign', signature)

	# This is for version 2 and more
	def _auth_extended(self, request, path, query):
		self._auth_basic(request, path, (path[2:] + "\0").encode('utf-8') + query)

	def call(self, path, args={}, auth=True, secure=True, parse=True):
		"""
		This method call the mtgox API, authenticating the request if necessary
		and return the result to the user

		Parameters
		----------
		path: str
			The path to call, including the API version. eg. 2/money/info
		args: map
			A map of arguments to provide to the API
		auth: bool
			Wether to authenticate the query or not. Is automatically set to
			False if api_key is None.
		secure: bool
			Use https for the API call, default is True
		parse: bool
			Decode the JSON data returned by the server, default is True

		Returns
		-------
		result: map
			A map using the format {'success': True, 'data': map or string} if
			the call was successful or {'success': False, 'code': int, 'reason': str}
			if the call failed

		Here is an example of a call manually disabling auth and json parsing:

		>>> api.call('2/BTCUSD/money/ticker', auth=False, parse=False)
		{'success': True, 'data': '<large blob of unparsed json>'}
		"""

		# disable auth if we are missing credential data
		if self.api_key == None or self.api_secret == None:
			auth = False

		# build the URL to call
		url = function_map_run('urlunsplit', (
			secure and 'https' or 'http',
			auth and 'mtgox.com' or 'data.mtgox.com',
			'api/' + path, '', ''
		))

		# add nonce in args (this should be the highest resolution timer you can find)
		# monotonic clock looks nice, but is python 3.3+ only
		if auth:
			args['nonce'] = int(int(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')) / 1000)

		# build the query string based on our arguments
		query = function_map_run('urlencode', args).encode('utf-8')

		# create a request to mtgox
		if query:
			request = function_map_run('create_request', url, query)
		else:
			request = function_map_run('create_request', url)
		# add a test user agent
		request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MtGox-Python%d/%s)' % (sys.version_info[0], mtgox.__version__))
		# take care of auth if necessary
		if auth:
			version = int(path[0])
			# default engine is the basic one
			auth_engine = getattr(self, self._default_auth)
			# retrieve the auth engine for the version of the API
			if version in self._versions:
				auth_engine = getattr(self, self._versions[version])
			auth_engine(request, path, query)
		# do the actual query
		data = None
		try:
			data = self._execute_request(request, parse)
		except URLError as err:
			return {'success': False, 'code': err.code, 'reason': err.reason}
		return {'success': True, 'data': data}

	def _execute_request(self, request, parse):
		data = None
		response = function_map_run('urlopen', request)
		data = response.read().decode("utf-8")
		if parse:
			data = json.loads(data)
		return data
