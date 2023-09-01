import json, os

from glitch import iframe_hack, transfer_motion_repeat
from randoscope import ffmpeg, rando_cut, s_to_f


def mkvid_snowday():
    # i = 0
    # while os.path.exists(f'{i}.mp4'):
    #     os.remove(f'{i}.mp4')
    #     i += 1
    cut_id = 'randocut14'
    vid_size = '1280:720'
    fps = 24
    audio_file = '01 The North Country - Snowday MASTER_MP3_320kbps.mp3'
    bpm = 92
    beat_dur = 60 / bpm
    cut_config = [
        # 9 bars of 4 beats
        [4,    9],
        # then 1 weird bar
        # yes, that's 5 beats and one sixteenth :|
        [5.25, 1],
        # pick up the pace
        [1,   16],
        # VERSE 1: crazy fast cuts
        [0.5, 24],
        # a little respite
        [1,    4],
        # back to crazy fast
        [0.5, 24],
        # the punchline
        [4,    1],
        # off-kilter
        [1.5,  4],
        [2,    1],
        [7.5,  1],
        # VERSE 2
        [0.5, 24],
        [1,    4],
        [0.5, 24],
        [4,    1],
        [2,    1],
        # OUTRO A
        [4,    8]
    ]
    cut_filename = f'{cut_id}_a.avi'
    rando_cut(
        cut_config, bpm, fps, vid_size, cut_filename,
        # infrequent i-frames for glitching
        ffmpeg_args='-c:v libxvid -q:v 1 -g 1000 -qmin 1 -qmax 1 -flags qpel+mv4',
    )

    # during outro A, remove all i-frames
    start_beat = sum([ beats*bars for beats,bars in cut_config[:-1] ])
    start_frame = s_to_f(start_beat * beat_dur, fps)
    glitch_vid = f'{cut_id}_a_glitch.avi'
    iframe_hack(start_frame, cut_filename, glitch_vid)
    os.remove(cut_filename)

    # outro B is new tempo
    bpm_outro = 85
    # get a randocut for outro B
    outro_cut_config = [[8,6]]
    outro_cut_filename = f'{cut_id}_b.mp4'
    offset = sum([ bars for beats,bars in cut_config ])
    rando_cut(outro_cut_config, bpm_outro, fps, vid_size, outro_cut_filename, offset=offset)
    # and apply the motion vectors from the last clip in outro A
    motion_vid = f'{offset-1}.mp4'
    content_vid = outro_cut_filename
    num_frames = s_to_f(cut_config[-1][0] * beat_dur, fps)
    outro_glitch_vid = f'{cut_id}_b_glitch.mpg'
    cut_interval = s_to_f(outro_cut_config[-1][0] * 60/bpm_outro, fps)
    transfer_motion_repeat(
        motion_vid, content_vid, outro_glitch_vid,
        fps, num_frames, vid_size,
        cut_interval=cut_interval
    )
    os.remove(outro_cut_filename)

    # recombine and add audio track
    start_offset = 0.3
    final_filename = f'{cut_id}.mp4'
    ffmpeg(f'''
      -i "{glitch_vid}"
      -i "{outro_glitch_vid}"
      -i "{audio_file}"
      -filter_complex "[0:v][1:v] concat=n=2:v=1:a=0, tpad=start_duration={start_offset} [outv]"
      -map [outv] -map 2:a -shortest
      "{final_filename}"
    ''', show_pbar=True)
    os.remove(glitch_vid)
    os.remove(outro_glitch_vid)


if __name__ == '__main__':
    mkvid_snowday()