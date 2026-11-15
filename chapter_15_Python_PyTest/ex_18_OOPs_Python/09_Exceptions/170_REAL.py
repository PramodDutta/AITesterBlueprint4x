import requests

try:
    url = input("Enter the url")
    response = requests.get(url=url)
    print(response.status_code)
except requests.exceptions.ConnectionError:
    print("Exception due to connection error")
except requests.exceptions.Timeout:
    print("Exception due to connection error")
except Exception as e:
    print(e)