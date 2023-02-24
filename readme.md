# randoscope

Search youtube for videos with titles that look like the default filenames from cameras and cut them together in tempo.

(random video idea stolen from https://default-filename-tv.neocities.org/)

## Installation

```
source install.sh
```

(Requires python3 and [ffmpeg](https://ffmpeg.org/))

## Usage

Activate the virtualenv:

```
source .venv/bin/activate
```

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
```

Do the thing:

```
rando_cut(cut_config, bpm, audio_file, fps, vid_size)
```

## ideas

- split screens
- curate videos
    - slack bot to vote? (veto)
- glitchy effect:
    - cut fast between 2 vids
    - speed manipulations
