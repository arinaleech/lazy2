import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser


async def fix_thumb(c_thumb):
    width, height = 0, 0
    try:
        if c_thumb is not None:
            metadata = extractMetadata(createParser(c_thumb))
            if metadata and metadata.has("width"):
                width = metadata.get("width")
            if metadata and metadata.has("height"):
                height = metadata.get("height")
            img = Image.open(c_thumb).convert("RGB")
            img = img.resize((320, height))
            img.save(c_thumb, "JPEG")  # Saving the resized image
    except Exception as e:
        print(f"Error in fix_thumb: {e}")
        c_thumb = None
       
    return width, height, c_thumb


async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = os.path.join(output_directory, f"{str(time.time())}.jpg")
    file_genertor_command = [
        "ffmpeg", "-ss", str(ttl), "-i", video_file, "-vframes", "1", out_put_file_name
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if os.path.lexists(out_put_file_name):
            return out_put_file_name
    except Exception as e:
        print(f"Error in take_screen_shot: {e}")
    return None


async def place_water_mark(input_file, output_file, water_mark_file):
    watermarked_file = output_file + ".watermark.png"
    try:
        metadata = extractMetadata(createParser(input_file))
        width = metadata.get("width", 0)
        shrink_watermark_file_genertor_command = [
            "ffmpeg", "-i", water_mark_file, "-y", "-v", "quiet",
            "-vf", f"scale={width}*0.5:-1", watermarked_file
        ]
        process = await asyncio.create_subprocess_exec(
            *shrink_watermark_file_genertor_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()

        commands_to_execute = [
            "ffmpeg", "-i", input_file, "-i", watermarked_file,
            "-filter_complex", "[0][1]overlay=10:10", output_file
        ]
        process = await asyncio.create_subprocess_exec(
            *commands_to_execute,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return output_file
    except Exception as e:
        print(f"Error in place_water_mark: {e}")
    return None


async def cult_small_video(video_file, output_directory, start_time, end_time):
    out_put_file_name = os.path.join(output_directory, f"{round(time.time())}.mp4")
    file_genertor_command = [
        "ffmpeg", "-i", video_file, "-ss", start_time, "-to", end_time,
        "-async", "1", "-strict", "-2", out_put_file_name
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        if os.path.lexists(out_put_file_name):
            return out_put_file_name
    except Exception as e:
        print(f"Error in cult_small_video: {e}")
    return None


async def generate_screen_shots(
    video_file,
    output_directory,
    is_watermarkable,
    wf,
    min_duration,
    no_of_photos
):
    metadata = extractMetadata(createParser(video_file))
    duration = 0
    if metadata and metadata.has("duration"):
        duration = metadata.get('duration').seconds
    if duration > min_duration:
        images = []
        ttl_step = duration // no_of_photos
        current_ttl = ttl_step
        for _ in range(no_of_photos):
            ss_img = await take_screen_shot(video_file, output_directory, current_ttl)
            if ss_img and is_watermarkable:
                ss_img = await place_water_mark(ss_img, os.path.join(output_directory, f"{str(time.time())}.jpg"), wf)
            images.append(ss_img)
            current_ttl += ttl_step
        return images
    else:
        print("Video duration is too short.")
        return None
