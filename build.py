#!/usr/bin/env python3
"""Render track.mp3: two hours of silence with short static bursts at random times.

The page plays this file on a loop from a random point, so the phone treats it like
music and keeps playing (iOS stops Web Audio that a timer tries to start).
Also writes schedule.json (burst start times, for the countdown) and test.mp3 (one burst).
"""
import array, json, random, subprocess

RATE = 16000
TOTAL = 2 * 60 * 60                  # seconds of track before it loops
GAP_MIN, GAP_MAX = 180, 420          # 3 to 7 minutes between bursts
LEN_MIN, LEN_MAX = 4.0, 6.5          # each burst lasts about 5 seconds
FADE = 1.5

raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'static.m4a', '-ac', '1', '-ar', str(RATE),
                      '-f', 's16le', '-'], capture_output=True, check=True).stdout
src = array.array('h', raw)


def burst(length):
    n = int(length * RATE)
    f = int(FADE * RATE)
    start = random.randrange(0, len(src) - n)
    out = array.array('h', src[start:start + n])
    for i in range(f):
        g = i / f
        out[i] = int(out[i] * g)
        out[n - 1 - i] = int(out[n - 1 - i] * g)
    return out


def encode(samples, path):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(RATE), '-ac', '1', '-i', '-',
                    '-c:a', 'libmp3lame', '-q:a', '6', path], input=samples.tobytes(), check=True)


track = array.array('h')
times = []
t = random.uniform(GAP_MIN, GAP_MAX) / 2     # half a gap at each end, so the loop point sounds like any other gap
while True:
    length = random.uniform(LEN_MIN, LEN_MAX)
    if t + length + GAP_MIN / 2 > TOTAL:
        break
    track.extend(array.array('h', bytes(2 * (int(t * RATE) - len(track)))))
    times.append(round(t, 2))
    track.extend(burst(length))
    t += length + random.uniform(GAP_MIN, GAP_MAX)
track.extend(array.array('h', bytes(2 * (TOTAL * RATE - len(track)))))

encode(track, 'track.mp3')
encode(burst(5.0), 'test.mp3')
json.dump({'duration': TOTAL, 'bursts': times}, open('schedule.json', 'w'))
print(len(times), 'bursts')
