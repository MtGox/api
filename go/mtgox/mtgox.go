package mtgox

import (
	"crypto/hmac"
	"crypto/sha512"
	"encoding/base64"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strconv"
	"strings"
	"time"
)

type AuthType int

const (
	Auto AuthType = iota
	Public
	Private
)

type Api struct {
	ApiKey    string
	ApiSecret string
	Auth      AuthType
	Debug     bool
}

type Request struct {
	HttpRequest *http.Request
	Path        string
	Parameters  url.Values
}

type InvalidVersion int8

func (version InvalidVersion) Error() string {
	return fmt.Sprintf("Invalid API version %d", int(version))
}

func NewApi(key, secret string) Api {
	return Api{key, secret, Auto, false}
}

func parseParameters(params map[string]interface{}) url.Values {
	parameters := url.Values{}
	for key, value := range params {
		// cast everyone to string
		switch value.(type) {
		case string:
			parameters.Add(key, value.(string))
		case int:
			parameters.Add(key, strconv.Itoa(value.(int)))
		case int64:
			parameters.Add(key, strconv.FormatInt(value.(int64), 10))
		case float64:
			parameters.Add(key, strconv.FormatFloat(value.(float64), 'f', -1, 64))
		// for 32bits computer (wat?)
		case float32:
			parameters.Add(key, strconv.FormatFloat(float64(value.(float32)), 'f', -1, 32))
		// booleans are converted to 0 or 1
		case bool:
			if value.(bool) {
				parameters.Add(key, "1")
			} else {
				parameters.Add(key, "0")
			}
		}
	}
	return parameters
}

func (api Api) Public() Api {
	api.Auth = Public
	return api
}

func (api Api) Private() Api {
	api.Auth = Private
	return api
}

func (api Api) Auto() Api {
	api.Auth = Auto
	return api
}

func (api Api) auth(request *Request) error {
	// extract api version number
	version, err := strconv.ParseInt(request.Path[0:1], 10, 8)
	if err != nil {
		return err
	}
	if version < 0 || version > 2 {
		return InvalidVersion(version)
	}

	// add the nonce value to the request parameters
	request.Parameters.Add("tonce", strconv.FormatInt(time.Now().UnixNano() / 1000, 10))

	// first decode secret
	b64 := base64.StdEncoding
	secret, err := b64.DecodeString(api.ApiSecret)
	if err != nil {
		return err
	}

	// the data we want to encode
	encodedData := request.Parameters.Encode()
	if version == 2 {
		// version 2 add the pathname for more entropy
		encodedData = request.Path[2:] + "\x00" + encodedData
	}

	// retrieve a sha512 hmac generator
	hmac := hmac.New(sha512.New, secret)
	// write our encoded data
	hmac.Write([]byte(encodedData))
	signature := b64.EncodeToString(hmac.Sum(nil))

	// add headers to request
	request.HttpRequest.Header.Add("Rest-Key", api.ApiKey)
	request.HttpRequest.Header.Add("Rest-Sign", signature)

	return nil
}

func (api Api) Call(path string, params map[string]interface{}) (string, error) {
	if params == nil {
		params = map[string]interface{}{}
	}
	// remove leading slashes in path
	path = strings.TrimLeft(path, "/")
	// setup parameter list
	parameters := parseParameters(params)

	// create request
	request := Request{nil, path, parameters}

	// default call URL
	url, err := url.Parse("https://data.mtgox.com/api/" + path)
	if err != nil {
		return "", err
	}

	// do auth only if key+secret are provided
	if api.Auth == Private || (api.Auth == Auto && api.ApiKey != "" && api.ApiSecret != "") {
		// because we need to authenticate, data.mtgox.com won't work
		url.Host = "mtgox.com"
		request.HttpRequest, err = http.NewRequest("POST", url.String(), nil)
		if err != nil {
			return "", err
		}
		// then run auth
		err := api.auth(&request)
		if err != nil {
			return "", err
		}
		// kinda hackish, but well
		postBuffer := strings.NewReader(request.Parameters.Encode())
		request.HttpRequest.Body = ioutil.NopCloser(postBuffer)
		request.HttpRequest.ContentLength = int64(postBuffer.Len())
		// don't forget to setup header for POST data
		request.HttpRequest.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	} else {
		// if we have any parameters, encode them in the URI
		if len(parameters) > 0 {
			url.RawQuery = parameters.Encode()
		}
		request.HttpRequest, err = http.NewRequest("GET", url.String(), nil)
		if err != nil {
			return "", err
		}
	}

	// debug stuff
	if api.Debug {
		fmt.Println("Output:")
		dump, err := httputil.DumpRequestOut(request.HttpRequest, true)
		if err != nil {
			return "", err
		}
		fmt.Println(string(dump))
	}

	// now do the query
	client := &http.Client{}
	resp, err := client.Do(request.HttpRequest)
	if err != nil {
		return "", err
	}

	// everything is good! read the response
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	return string(body), nil
}
