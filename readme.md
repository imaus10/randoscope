# randoscope

Search youtube for videos with titles that look like the default filenames from cameras and cut them together in tempo.

(random video idea stolen from https://default-filename-tv.neocities.org/)

## Installation

```
source install.sh
```

(Requires python3 and [homebrew](https://brew.sh/))

## Usage

Define the song and video parameters:

```
cut_config = [
    # 9 bars of 4 beats
    [4, 9],
    # then 1 weird bar
    # yes, that's 5 beats and one sixteenth :|
    [5.25, 1],
    # pick up the pace
    [1, 16],
    # crazy fast cuts
    [0.5, 24],
    # a little respite
    [1, 4],
    # back to crazy fast
    [0.5, 24],
    # the punchline
    [4, 1]
]
bpm = 92
audio_file = '01 The North Country - Snowday MASTER_MP3_320kbps.mp3'
fps = 24
vid_size = '1280:720'
out_filename = 'snow_day_randocut.mp4'
```

Do the thing:

```
from randoscope import rando_cut
rando_cut(cut_config, bpm, audio_file, fps, vid_size, out_filename)
```

## ideas

- titles "exquisite corpse" and "(born at the right time)"
- split screens mouth
- regenerate a few times, choose the best one (make sure metadata capture is working first)
- glitchy effect:
    - cut fast between 2 vids
    - speed manipulations
