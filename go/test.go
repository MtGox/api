package main

import (
	"./mtgox"
	"encoding/json"
	"flag"
	"log"
	"os"
)

var flagKey = flag.String("key", "", "your api key")
var flagSecret = flag.String("secret", "", "your api secret")

// used for .apirc
type Credentials struct {
	Key    string
	Secret string
}

func main() {
	var key, secret string

	// small prefix for output
	log.SetPrefix("mtgox-go ")

	// parse command-line
	flag.Parse()

	if *flagKey == "" || *flagSecret == "" {
		// check if .apirc exists in the main path, and load credentials from it if necessary
		file, err := os.Open("../.apirc")
		if err == nil {
			// file is here, parse it
			dec := json.NewDecoder(file)
			var cred Credentials
			if err := dec.Decode(&cred); err == nil {
				key = cred.Key
				secret = cred.Secret
			}
			file.Close()
		}
	} else {
		key = *flagKey
		secret = *flagSecret
	}

	// instanciate mtgox Api
	api := mtgox.NewApi(key, secret)
	// call test Api, by adding Public() we disable auth and hit on data.mtgox.com (faster)
	result, err := api.Public().Call("2/BTCUSD/money/ticker", nil)
	// catch errors
	if err != nil {
		log.Fatal(err)
	}
	// give us the output
	log.Println(result)

	// do the same with the private API if a key/secret was found
	if key != "" {
		// now the private API, because Public() create a copy of the api, we don't need to
		// call Private() for this call, the class will detect that a key/secret are set and
		// will automatically sign the request
		result, err = api.Call("2/money/info", nil)
		// catch errors
		if err != nil {
			log.Fatal(err)
		}
		// give us the output
		log.Println(result)
	}
}
