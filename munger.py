import argparse
import datetime
import os
import re

powertap = '2013-06-27 16-34-57.tcx'
garmin = '6-26-13 4-35-01 PM.tcx'

parser = argparse.ArgumentParser()
parser.add_argument('powertap', help='The file you exported from PowerAgent')
parser.add_argument('garmin', help='The file you exported from Training Center')
values = parser.parse_args()

powertap = values.powertap
garmin = values.garmin

time_re = re.compile('<Time>([\d:TZ-]+)</Time>')
watts_re = re.compile('<Watts>([\d]+)</Watts>')
torque_re = re.compile('<TorqueNewtonMeters>([\d\.]+)</TorqueNewtonMeters>')
extensions_re = re.compile('<Extensions>')
id_re = re.compile('<Id>(.*)<\/Id>')

def find_start_time(f):
    for line in f:
        m = id_re.search(line)
        if m:
            return datetime.datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%SZ')

with open(powertap, 'r') as f:
    powertap_start = find_start_time(f)
with open(garmin, 'r') as f:
    garmin_start = find_start_time(f)

garmin_offset = garmin_start - powertap_start

print 'powertap start', powertap_start
print 'garmin start', garmin_start

with open(powertap, 'r') as f:
    power_lines = f.readlines()

power_data = {}

timestamp = None
watts = None
torque = None
for line in power_lines:
    if timestamp is None:
        m = time_re.search(line)
        if m:
            timestamp = datetime.datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%SZ')
    elif watts is None:
        m = watts_re.search(line)
        if m:
            watts = m.group(1)
    elif torque is None:
        m = torque_re.search(line)
        if m:
            torque = m.group(1)

    if timestamp is not None and watts is not None and torque is not None:
        power_data[timestamp] = (watts, torque)
        timestamp = None
        watts = None
        torque = None

with open(garmin, 'r') as f:
    garmin_lines = f.readlines()

actual_power_numbers = 0
missing_power_numbers = 0
insertion_work = {}
timestamp = None
extensions_line_no = None
power_numbers = (0, 0)
for line_num, line in enumerate(garmin_lines):
    if timestamp is None:
        m = time_re.search(line)
        if m:
            timestamp = datetime.datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%SZ')
            timestamp = timestamp - garmin_offset
    if extensions_line_no is None:
        m = extensions_re.search(line)
        if m:
            extensions_line_no = line_num

    if timestamp is not None and extensions_line_no is not None:
        if timestamp in power_data:
            power_numbers = power_data[timestamp]
            actual_power_numbers += 1
        else:
            # we use the last known values. shitty.
            #print 'Missing', timestamp
            missing_power_numbers += 1
        insertion_work[extensions_line_no] = """\
<TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
<Watts>%s</Watts>
</TPX>
<TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">
<TorqueNewtonMeters>%s</TorqueNewtonMeters>
</TPX>
""" % power_numbers
        timestamp = None
        extensions_line_no = None

lines_to_append_after = insertion_work.keys()
lines_to_append_after.sort(lambda x, y: cmp(y,x))
for line_num in lines_to_append_after:
    garmin_lines.insert(line_num + 1, insertion_work[line_num])

print 'All done'
print 'Got power right for %d trackpoints' % (actual_power_numbers,)
print 'Got it wrong for %d' % (missing_power_numbers,)

with open('munged-%s' % (os.path.basename(powertap),), 'w') as f:
    # This stripping is undoubtedly slow. But it appears to save about 1MB/hour
    # of riding. And that's a big win.
    for line in garmin_lines:
        f.write(line.strip() + '\n')

