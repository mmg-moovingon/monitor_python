#!/usr/bin/env python

from __future__ import print_function
import sys
import json

try:
    # For Python 3
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    # For Python 2
    from urllib2 import Request, urlopen, URLError, HTTPError

def main():
    url = "http://localhost:8080/bidder/?bid=aaaaa"
    json_data = {
        "id": "1234567893",
        "imp": [
            {
                "id": "1",
                "video": {
                    "mimes": ["video/mp4"],
                    "linearity": 1,
                    "minduration": 5,
                    "maxduration": 30,
                    "protocol": [2, 5]
                }
            }
        ],
        "site": {
            "page": ""
        },
        "device": {
            "carrier": "o2 - de1",
            "ip": "24.234.255.255",
            "dpidsha1": "AA000DFE74168477C70D291f574D344790E0BB11"
        },
        "user": {
            "uid": "456789876567897654678987656789",
            "buyeruid": "545678765467876567898765678987654"
        }
    }

    try:
        # Convert the json_data to a JSON string and encode it
        data = json.dumps(json_data).encode('utf-8')
        headers = {'Content-Type': 'application/json'}

        # Create a Request object
        req = Request(url, data=data, headers=headers)

        # Send the request and get the response
        response = urlopen(req)
        status_code = response.getcode()

        if status_code == 200:
            # Read the response data
            response_data = response.read().decode('utf-8')

            # Parse the JSON response
            response_json = json.loads(response_data)

            # Get the value of the "id" key
            id_value = response_json.get("id")

            # Check if the id value matches the specified values
            if id_value in ["1234567893", "e27605b1-ab55-4b2d-93c0-87953989f434"]:
                print("1")
            else:
                print("0")
        else:
            print("0")
    except Exception as e:
        print("0")

if __name__ == "__main__":
    main()