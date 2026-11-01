response_times_ms = [1200, 1500, 1800]

# def mil_sec(x):
#     return x / 1000
# response_times_ms_list = list(map(mil_sec, response_times_ms))

response_times_ms_list = list(map(lambda x:x/1000, response_times_ms))
print(response_times_ms_list)