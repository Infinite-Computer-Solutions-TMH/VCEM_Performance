import requests
import json
from rich.console import Console

def set_parameter_values(auth_token):
    url = "http://101.101.63.49/api/tr069/setParameterValues/1878D4-vSpeed-NUC-simulator-BOT010236?async=false"

    payload = json.dumps({
      "options": {
        "priority": 100,
        "expirationTimeoutSeconds": 180,
        "updateCachedDataRecord": True,
        "disableCaptureConstraint": True,
        "triggerCR": True
      },
      "function": {
        "name": "SetParameterValues",
        "parameters": [
          {
            "name": "Device.DeviceInfo.Manufacturer",
            "type": "string",
            "value": "VZ",
            "notificationChange": False
          }
        ]
      }
    })
    headers = {
      'Authorization': f'Bearer {auth_token}',
      'Content-Type': 'application/json'
    }

    # response = requests.request("POST", url, headers=headers, data=payload)
    response = requests.post(url, headers=headers, data=payload)




    print("----------------------------------**SPV**-------------------------------------------------")
    print(f"status code {response.status_code}")
    print(response.text)
