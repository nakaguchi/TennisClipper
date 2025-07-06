import os

import cv2
import ffmpeg
import numpy as np
import pandas as pd

play_time_threshold = 5.0  # Minimum play time to consider a segment
match_size = (320, 240)  # 一致度算出のサイズ


def get_video_info(in_file):
    """Probe a video file and print its metadata."""
    probe = ffmpeg.probe(in_file)
    video_streams = [
        stream for stream in probe["streams"] if stream["codec_type"] == "video"
    ]
    in_duration = video_streams[0]["duration"]
    in_width = video_streams[0]["width"]
    in_height = video_streams[0]["height"]
    in_fps = eval(video_streams[0]["r_frame_rate"])
    csv_file = in_file.replace(".ts", ".csv")
    tmpl_file = in_file.replace(".ts", ".jpg")
    out_file = in_file.replace(".ts", ".mp4")

    # print(f"Input video: {in_file}")
    # print(f"  Duration: {in_duration} sec")
    # print(f"  Resolution: {in_width}x{in_height}")
    # print(f"  FPS: {in_fps}")

    return {
        "input": in_file,
        "duration": in_duration,
        "width": in_width,
        "height": in_height,
        "fps": in_fps,
        "csv": csv_file,
        "tmpl": tmpl_file,
        "output": out_file,
    }


def calc_threshold(data):
    """Calculate the threshold for the given CSV data using Otsu's method."""
    bins = 100
    hist, bin_range = np.histogram(data, bins=bins, range=(0, 1))
    bin = [(bin_range[i] + bin_range[i + 1]) / 2 for i in range(len(bin_range) - 1)]

    total = np.sum(hist)
    sumB = 0.0  # Background sum
    sum1 = np.sum(bin * hist)  # Total sum of all bins
    wB = 0.0  # Background weight
    max_var = 0.0  # Maximum variance
    n = len(hist)
    threshold_list = []  # Initial threshold
    for ii in range(n):
        wF = total - wB  # Foreground weight
        if wF > 0 and wB > 0:
            mF = (sum1 - sumB) / wF  # Foreground mean
            var = wB * wF * ((sumB / wB) - mF) ** 2  # Variance
            if var > max_var:
                max_var = var
                threshold_list.append(bin[ii])
            elif var == max_var:
                threshold_list.append(bin[ii])
        wB += hist[ii]  # Update background weight
        sumB += bin[ii] * hist[ii]  # Update background sum

    print(f"Calculated threshold: {np.mean(threshold_list):.3f}")
    return np.mean(threshold_list)


def make_segments(info):
    """Read a CSV file and return segments based on the count."""
    segments = []
    in_play = False

    csv_data = pd.read_csv(info["csv"])
    if csv_data.empty:
        print("CSV file is empty or does not exist.")
        exit(1)

    threshold = calc_threshold(csv_data["zncc"])

    csv_data = csv_data[["count", "zncc"]]
    csv_data = csv_data.dropna()  # Remove rows with NaN values

    for index, row in csv_data.iterrows():
        count = int(row["count"])
        zncc = float(row["zncc"])
        if not in_play and zncc >= threshold:
            start_time = count / info["fps"]
            in_play = True
        if in_play and zncc < threshold:
            end_time = (count - 1) / info["fps"]
            play_time = end_time - start_time
            if (
                play_time > play_time_threshold
            ):  # Only add segments longer than 5 seconds
                print(f"Segment: {play_time:.2f} sec")
                segments.append((start_time, end_time - start_time))
            in_play = False
    return segments


def edit_video(info, segments):
    # 一時ファイル名リスト
    temp_files = []

    # 各区間を切り出して一時ファイルに保存
    for i, (start, dulation) in enumerate(segments):
        temp_file = f"temp{i:04}.mp4"
        (
            ffmpeg.input(in_file, ss=start, t=dulation, r=info["fps"])
            .output(temp_file, pix_fmt="yuv420p", **{"b:v": "2000k"})
            .run(overwrite_output=True)
        )
        temp_files.append(temp_file)

    # 一時ファイルを結合
    list_file = "filelist.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    # concat demuxerで結合
    (
        ffmpeg.input(list_file, format="concat", safe=0)
        .output(info["output"], c="copy")
        .run(overwrite_output=True)
    )

    # 一時ファイルの削除（必要に応じて）
    for temp_file in temp_files:
        os.remove(temp_file)
    os.remove(list_file)


def make_csv(info):
    # Open the input video file with ffmpeg
    cap = (
        ffmpeg.input(info["input"], ss=0, t=info["duration"])
        .output("pipe:", format="rawvideo", pix_fmt="rgb24")
        .run_async(pipe_stdout=True)
    )

    # Open the template image
    template_image = cv2.imread(info["tmpl"])
    template_image = cv2.cvtColor(template_image, cv2.COLOR_BGR2RGB)
    template_image = cv2.resize(
        template_image, match_size, interpolation=cv2.INTER_LINEAR
    )

    similarity = pd.DataFrame()  # DataFrame to store similarity results

    # with open(out_csv, "w", newline="") as csvfile:
    #     csvWriter = csv.writer(csvfile)
    #     csvWriter.writerow(["count", "diff", "ssim", "zncc"])  # ヘッダー行

    count = 0
    while True:
        in_bytes = cap.stdout.read(info["width"] * info["height"] * 3)
        if not in_bytes:
            break
        # print(f"{count / in_fps} / {in_duration}sec  ")
        in_frame = np.frombuffer(in_bytes, np.uint8).reshape(
            [info["height"], info["width"], 3]
        )
        in_frame_s = cv2.resize(in_frame, match_size, interpolation=cv2.INTER_LINEAR)

        # diff = calc_diff(in_frame_s, template_image)
        diff = 0
        # ssim = calc_ssim(in_frame_s, template_image)
        ssim = 0
        corr = calc_cross_correlation(in_frame_s, template_image)
        # csvWriter.writerow([count, diff, ssim, corr])  # 書き込み
        addition = pd.DataFrame(
            [[count, diff, ssim, corr]],
            columns=["count", "diff", "ssim", "zncc"],
        )
        similarity = pd.concat([similarity, addition], ignore_index=True)
        count += 1
    cap.wait()
    similarity.to_csv(info["csv"], index=False)


def calc_diff(img1, img2):
    """Calculate the difference between two images."""
    diff = cv2.absdiff(img1, img2)
    return (
        np.sum(diff) / (img1.shape[0] * img1.shape[1] * 3) / 100
    )  # Normalize by pixel count


def calc_ssim(img1, img2):
    """Calculate SSIM (Structural Similarity Index) between two images."""
    ssim_rgb, _ = cv2.quality.QualitySSIM_compute(img1, img2)
    return np.mean(ssim_rgb)


def calc_cross_correlation(img1, img2):
    """Calculate cross-correlation between two images."""
    img1f = img1.astype(np.float32)
    img2f = img2.astype(np.float32)
    correlation = cv2.matchTemplate(img1f, img2f, cv2.TM_CCOEFF_NORMED)
    return np.mean(correlation)


if __name__ == "__main__":
    target_dir = R"D:\usr\DL"
    files = os.listdir(target_dir)
    files = [f for f in files if f.endswith(".ts")]
    for in_file in files:
        info = get_video_info(os.path.join(target_dir, in_file))
        if os.path.exists(info["output"]):
            continue
        if not os.path.exists(info["csv"]):
            make_csv(info)
        segments = make_segments(info)
        edit_video(info, segments)
