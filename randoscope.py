import os
import random
import shlex
import subprocess

from tqdm import tqdm
from yt_dlp import YoutubeDL


def ffmpeg(multiline_cmd, quiet=True, show_pbar=False):
    quiet_args = ['-v', 'warning'] if quiet else []
    if show_pbar:
        quiet_args.append('-stats')
    cmd = [
        'ffmpeg',
        *quiet_args,
        *shlex.split(multiline_cmd.replace('\n', ''))
    ]
    subprocess.run(cmd, check=True)


def dl_rando_vid(vid_file, cut_dur):
    '''
    Generate a random filename that looks like it came straight from a camera,
    then search youtube and download a random clip from it.
    '''
    # idea stolen from https://default-filename-tv.neocities.org/
    prefix = random.choice(['DSC', 'MOV', 'IMG', '100', 'MVI'])
    separator = random.choice([' ', '_', ''])
    number = random.randint(0, 9999)
    rando_query = f'{prefix}{separator}{number:04}'

    # first get the video duration
    ytdl_opts = {
        'default_search' : 'ytsearch1',
        'noplaylist'     : True,
        'format'         : 'mp4',
        'quiet'          : True,
    }
    with YoutubeDL(ytdl_opts) as ytdl:
        try:
            vid_info = ytdl.extract_info(rando_query, download=False)
        except:
            return False

    # then choose a random location in the video and download it
    vid_dur = vid_info['entries'][0]['duration']
    url = vid_info['entries'][0]['url']
    if vid_dur < cut_dur:
        return False
    ceiling = vid_dur - (int(cut_dur)+1)
    random_location = random.randint(0, ceiling)
    ffmpeg(f'-ss {random_location} -i "{url}" -t {cut_dur} {vid_file}')
    return True


def s_to_f(seconds, fps):
    '''
    Convert seconds to number of frames (at static FPS).
    '''
    num_frames = int(seconds * fps)
    return num_frames


def rando_cut(cut_config, bpm, audio_file, fps, vid_size):
    beat_dur = 60 / bpm

    vid_count = 0
    vid_files = []
    crop_cmds = []
    concat_inputs = ''
    total_dur = 0
    pbar = tqdm(total=sum([ cut[1] for cut in cut_config ]))
    for beats_per_cut, num_cuts in cut_config:
        dur = beats_per_cut * beat_dur
        for _ in range(num_cuts):
            vid_file = f'{vid_count}.mp4'
            vid_files.append(vid_file)
            dl_success = False
            while not dl_success:
                dl_success = dl_rando_vid(vid_file, dur)
            num_frames = s_to_f(total_dur + dur, fps) - s_to_f(total_dur, fps)
            total_dur += dur
            concat_input = f'[v{vid_count}]'
            crop_cmds.append(f'''[{vid_count}:v]
                fps={fps},
                trim=end_frame={num_frames},
                scale={vid_size}:force_original_aspect_ratio=increase,
                crop={vid_size},
                setsar=1
            {concat_input}''')
            concat_inputs += concat_input
            vid_count += 1
            pbar.update()
    pbar.close()

    ffmpeg_inputs = ' '.join([ f'-i {vid_file}' for vid_file in vid_files ])
    spaces = ' '*8
    nl = f';\n{spaces}'
    crop_cmds = nl.join(crop_cmds)
    ffmpeg(f'''
      {ffmpeg_inputs}
      -i "{audio_file}"
      -filter_complex
       "{crop_cmds};
        {concat_inputs} concat=n={vid_count}:v=1:a=0, tpad=start_duration=0.3 [outv]"
      -map "[outv]" -map {vid_count}:a -shortest
      randocut8.mp4
    ''', show_pbar=True)
    for vid_file in vid_files:
        subprocess.run(f'rm {vid_file}', shell=True, check=True)

if __name__ == '__main__':
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
    rando_cut(cut_config, bpm, audio_file, fps, vid_size)

