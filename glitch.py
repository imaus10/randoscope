import json, os

from randoscope import ffmpeg, get_crop


def iframe_hack(start_frame, filename_in, filename_out):
    # 0x30306463 signals the end of a frame.
    frame_header = bytes.fromhex('30306463')
    # 0x0001B0 signals the beginning of an iframe
    iframe = bytes.fromhex('0001B0')
    # 0x0001B6 signals a pframe
    pframe = bytes.fromhex('0001B6')
    with open(filename_in, 'rb') as in_file:
        frames = in_file.read().split(frame_header)
    end_frame = frames.pop()

    with open(filename_out, 'wb') as out_file:
        # write header
        out_file.write(frames.pop(0))

        for index, frame in enumerate(frames):
            # remove i-frames til the end
            if index >= start_frame:
                frame_type = frame[5:8]
                if frame_type == iframe:
                    # use the last frame to keep song alignment
                    frame = last_frame
            # add back the frame separator token
            out_file.write(frame_header + frame)
            last_frame = frame


def transfer_motion_repeat(
    input_motion_vid, input_content_vid, output_vid,
    fps, num_frames, vid_size,
    cut_interval=1000
):
    cropped_vid = 'motion_vid.mp4'
    ffmpeg(f'''
      -i "{input_motion_vid}"
      -vf "{get_crop(fps, num_frames, vid_size)}"
      {cropped_vid}
    ''', show_pbar=True)
    # extract motion data using ffedit
    motion_vid = 'motion_vid.mpg'
    ffgac(f'''
      -i {cropped_vid} -an
      -mpv_flags +nopimb+forcemv -qscale:v 0 -g 1000
      -vcodec mpeg2video -f rawvideo -y
      {motion_vid}
    ''')
    os.remove(cropped_vid)
    motion_json = 'motion.json'
    ffedit(f'-i {motion_vid} -f mv:0 -e {motion_json}')
    os.remove(motion_vid)

    # grab the motion vector in each frame
    with open(motion_json, 'r') as f:
        raw_data = json.load(f)
    os.remove(motion_json)
    frames = raw_data['streams'][0]['frames']
    vectors = []
    for frame in frames:
        try:
            vectors.append(frame['mv']['forward'])
        except:
            vectors.append([])

    # prepare the pixel content video
    content_vid = 'content_vid.mpg'
    ffgac(f'''
      -i {input_content_vid}
      -an -mpv_flags +nopimb+forcemv -qscale:v 0 -g {cut_interval}
      -vcodec mpeg2video -f rawvideo -y
      {content_vid}
    ''')

    # assemble a JS script string to apply the motion vectors
    # TODO: new versions of ffedit support python script inputs...
    script_contents = '''
        var vectors = ''' + json.dumps(vectors) + ''';
        var n_frames = 0;

        function glitch_frame(frame) {
            frame["mv"]["overflow"] = "truncate";
            let fwd_mvs = frame["mv"]["forward"];
            if (fwd_mvs && vectors[n_frames]) {
                for ( let i = 0; i < fwd_mvs.length; i++ ) {
                    let row = fwd_mvs[i];
                    for ( let j = 0; j < row.length; j++ ) {
                        let mv = row[j];
                        try {
                            mv[0] += vectors[n_frames][i][j][0];
                            mv[1] += vectors[n_frames][i][j][1];
                        } catch {}
                    }
                }
            }

            n_frames = (n_frames+1) % ''' + str(cut_interval) + ''';
        }
    '''
    # write the code to a .js file
    # and apply the script
    script_path = 'apply_vectors.js'
    with open(script_path, 'w') as f:
        f.write(script_contents)
    ffedit(f'-i {content_vid} -f mv -s {script_path} -o {output_vid}')
    os.remove(script_path)
    os.remove(content_vid)


def ffgac(multiline_cmd, **kwargs):
    ffmpeg(multiline_cmd, alt_binary='ffgac', **kwargs)


def ffedit(multiline_cmd, **kwargs):
    ffmpeg(multiline_cmd, alt_binary='ffedit', **kwargs)