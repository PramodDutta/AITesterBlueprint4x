def vwo_login(user):
    if user!= "admin":
        raise Exception("You are not admin, not auth.")
    return "Welcome Admin"

# print(vwo_login("pramod"))
print(vwo_login("admin"))