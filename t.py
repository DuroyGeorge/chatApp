import datetime

# 获取当前的日期和时间
now = datetime.datetime.now()

# 格式化时间为年-月-日 时:分
formatted_time = now.strftime("%m-%d %H:%M")

# 打印格式化后的时间
print("Current time (up to the minute):", formatted_time)
