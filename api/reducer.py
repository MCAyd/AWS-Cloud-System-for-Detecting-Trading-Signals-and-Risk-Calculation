#!/usr/bin/python3
import sys

days = {}

# using STDIN
for line in sys.stdin:
	parts = line.strip().split() # split on whitespace
	current_day, s95, s99 = parts
	s95 = float(s95)
	s99 = float(s99)

	index = int(current_day)

	if index not in days:
		days[index] = [0, 0, 0]

	days[index][0] += s95
	days[index][1] += s99
	days[index][2] += 1

for index in sorted(days.keys()):
	print(index, "\t", days[index][0]/days[index][2], days[index][1]/days[index][2])
