from datetime import datetime

# start time and end time
start_time = datetime.strptime("2:00 pm", "%I:%M %p")
end_time = datetime.strptime("2:30 pm", "%I:%M %p")

# get difference
delta = end_time - start_time

sec = delta.total_seconds()
print('difference in seconds:', sec)

min = sec / 60
print('difference in minutes:', min)

# get difference in hours
hours = sec / (60 * 60)
print('difference in hours:', hours)
