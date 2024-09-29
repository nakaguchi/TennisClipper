import pprint

import cv2
import ffmpeg
import numpy as np
from PIL import Image

threshold = 50.0
start_time = 0


def video_to_video(in_file, out_file, tmpl_file):
    probe = ffmpeg.probe(in_file)
    pprint.pp(probe)
    video_streams = [
        stream for stream in probe["streams"] if stream["codec_type"] == "video"
    ]
    in_duration = video_streams[0]["duration"]
    in_width = video_streams[0]["width"]
    in_height = video_streams[0]["height"]
    in_fps = int(eval(video_streams[0]["r_frame_rate"]))
    out_width = 1440
    out_height = 810

    cap = (
        ffmpeg.input(in_file, ss=start_time, t=in_duration)
        .output("pipe:", format="rawvideo", pix_fmt="rgb24")
        .run_async(pipe_stdout=True)
    )

    writer = (
        ffmpeg.input(
            "pipe:",
            format="rawvideo",
            pix_fmt="rgb24",
            s="{}x{}".format(out_width, out_height),
            r=in_fps,
        )
        .output(out_file, pix_fmt="yuv420p", **{"b:v": "1000k"})
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    template_image = cv2.imread(tmpl_file)
    count = 0
    while True:
        in_bytes = cap.stdout.read(in_width * in_height * 3)
        if not in_bytes:
            break
        in_frame = np.frombuffer(in_bytes, np.uint8).reshape([in_height, in_width, 3])
        diff = np.sum(cv2.absdiff(in_frame, template_image)) / (in_width * in_height)
        # cv2.imwrite(f"img{count:04}.jpg", in_frame)
        # print(f"img{count:04}  ", np.sum(diff) / (width * height))
        count += 1
        if count % in_fps == 0:
            print(f"{count / in_fps} / {in_duration}sec  ")

        if diff < threshold:
            out_frame = Image.fromarray(in_frame).resize(
                (out_width, out_height), Image.Resampling.BILINEAR
            )
            writer.stdin.write(np.array(out_frame).astype(np.uint8).tobytes())

    writer.stdin.close()
    cap.wait()
    writer.wait()


if __name__ == "__main__":
    in_file = "./nishioka.ts"
    out_file = "./nishioka_edit.mp4"
    tmpl_file = "./template.jpg"
    video_to_video(in_file, out_file, tmpl_file)
