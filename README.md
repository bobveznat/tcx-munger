tcx-munger
==========

I use this to glue together tcx files from my old Powertap SL and my
Garmin Edge 500.

I begin by downloading my ride from both devices. I use Garmin Training
Center for the Edge and Cycleops' PowerAgent for the Powertap. In each I
select the activity I just downloaded and export as a tcx file. Then I
run the script giving those two tcx file as parameters. The output .tcx
file is then the Garmin file augmented with the power and torque numbers
from the Powertap file.

Like so (the powertap file goes first):

  python munger.py ../Documents/2013-06-23\ 13-54-40.tcx ../Documents/6-23-13\ 1-54-47\ PM.tcx

Implementation Details
======================

I don't do anything fancy for syncing the devices. I assume that the
clocks on the two devices are more or less accurate (to within a second
or two) and that you started the ride on both devices within a second or
two of each other. The idea isn't to get a perfect match of speed
(garmin), cadence (garmin) and power (powertap). It's just to more or
less line them up. All of that said the algorithm is trivial: loop over
every trackpoint in the Garmin file and for each timestamp go find the
time in the powertap file that matches.

What you'll see then is that the Powertap actually doesn't record once
per second. In fact it records 48 times a second, not 60. So there are
12 gaps per minute to fill in. To compensate for this I assume that
whatever power and torque you were holding on the last trackpoint is
what you were still holding. A better solution might be to lookahead and
average the next point.


