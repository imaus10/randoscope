import os
import random
import shlex
import subprocess

import cv2
from tqdm import tqdm
from yt_dlp import YoutubeDL


def dl_rando_vid(vid_file, cut_dur):
    '''
    Generate a random filename that looks like it came straight from a camera,
    then search youtube and download a random clip from it.
    idea stolen from https://default-filename-tv.neocities.org/
    '''
    while True:
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
                continue

        # then choose a random location in the video and download it
        vid_info = vid_info['entries'][0]
        vid_dur = vid_info['duration']
        dl_url = vid_info['url']
        url = vid_info['webpage_url']
        if vid_dur < cut_dur:
            continue
        # make sure there's one second on the end
        # (sometimes we get videos that are cut slightly short)
        ceiling = vid_dur - int(cut_dur) - 1
        random_location = random.randint(0, ceiling)
        metadata = f'''
            {vid_file}
            ======
            query: {rando_query}
            url: {url}
            time: {random_location}s for {cut_dur}s
            ======
        '''
        try:
            ffmpeg(f'''
              -ss {random_location} -i "{dl_url}" -t {cut_dur} -an
              -metadata description="{metadata}"
              {vid_file}
            ''')
        except:
            continue
        return metadata


def rando_cut(
    cut_config, bpm, fps, vid_size, out_filename,
    is_curated=True, filename_offset=0, ffmpeg_args=''
):
    beat_dur = 60 / bpm
    vid_files = []
    crop_cmds = []
    concat_inputs = ''
    all_metadata = ''
    total_dur = 0
    vid_count = 0
    pbar = tqdm(total=sum([ cut[1] for cut in cut_config ]))
    for beats_per_cut, num_cuts in cut_config:
        dur = beats_per_cut * beat_dur
        for _ in range(num_cuts):
            vid_file = f'{vid_count+filename_offset}.mp4'
            while not os.path.exists(vid_file):
                metadata = dl_rando_vid(vid_file, dur)
                if is_curated:
                    choice = 'r'
                    while choice == 'r':
                        play_video(vid_file, fps)
                        choice = ''
                        while choice not in ('y','n','r'):
                            choice = input('Keep? (y)es / (n)o / (r)eplay ').lower()
                    if choice == 'n':
                        os.remove(vid_file)
                    else:
                        all_metadata += metadata
            vid_files.append(vid_file)
            num_frames = s_to_f(total_dur + dur, fps) - s_to_f(total_dur, fps)
            total_dur += dur
            concat_input = f'[v{vid_count}]'
            crop_cmds.append(f'[{vid_count}:v] {get_crop(fps, num_frames, vid_size)} {concat_input}')
            concat_inputs += concat_input
            vid_count += 1
            pbar.update()
    cv2.destroyAllWindows()
    pbar.close()

    ffmpeg_inputs = ' '.join([ f'-i {vid_file}' for vid_file in vid_files ])
    spaces = ' '*8
    nl = f';\n{spaces}'
    crop_cmds = nl.join(crop_cmds)
    ffmpeg(f'''
      {ffmpeg_inputs}
      -filter_complex
       "{crop_cmds};
        {concat_inputs} concat=n={vid_count}:v=1:a=0 [outv]"
      -map "[outv]"
      {ffmpeg_args}
      "{out_filename}"
    ''', show_pbar=True)
    # for vid_file in vid_files:
    #     os.remove(vid_file)


def ffmpeg(multiline_cmd, alt_binary=None, quiet=True, show_pbar=False):
    quiet_args = ['-v', 'warning'] if quiet else []
    if quiet and show_pbar and alt_binary != 'ffedit':
        quiet_args.append('-stats')
    cmd = [
        alt_binary or 'ffmpeg',
        *quiet_args,
        *shlex.split(multiline_cmd.replace('\n', ''))
    ]
    subprocess.run(cmd, check=True)


def get_crop(fps, num_frames, vid_size):
    return f'''
        fps={fps},
        trim=end_frame={num_frames},
        scale={vid_size}:force_original_aspect_ratio=increase,
        crop={vid_size},
        setsar=1
    '''


def s_to_f(seconds, fps):
    '''
    Convert seconds to number of frames (at static FPS).
    '''
    num_frames = int(seconds * fps)
    return num_frames


def play_video(vid_file, fps):
    vid = cv2.VideoCapture(vid_file)
    window_name = 'Randoscope'
    cv2.namedWindow(window_name)
    cv2.moveWindow(window_name, 0, 0)
    while vid.isOpened():
        success, frame = vid.read()
        if success:
            cv2.imshow(window_name, frame)
            cv2.waitKey(int(1000/fps))
        else:
            break
    vid.release()
