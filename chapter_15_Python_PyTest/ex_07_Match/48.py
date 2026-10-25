status = 900

match status:
    case 200 | 201:
        print("Request successful")
    case 400:
        print("Bad request")
    case 401:
        print("Unauthorized")
    case 500:
        print("Server error")
    case _:
        print("Unknown status")