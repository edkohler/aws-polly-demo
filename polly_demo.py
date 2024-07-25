import os
import pandas as pd
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, AudioFileClip, CompositeVideoClip, ColorClip, vfx, VideoClip, ImageClip, CompositeAudioClip, afx
import uuid
from moviepy.video.fx.resize import resize
from moviepy.audio.fx.volumex import volumex
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import sys
import psutil
import gc
from datetime import datetime
import requests
from urllib.parse import urlparse

# Load the quiz data
csv_file = "polly.csv"
quiz_data = pd.read_csv(csv_file)
original_filename = "polly_demo.mp4"
quiz_name = "Amazon Polly Voice Demonstrations - English Voices"


background_image = ImageClip('polly_background_image.jpg').set_duration(2) #Credit: Chiara Coetzee

background_image.write_videofile("background_image_video.mp4", codec='libx264', audio_codec='aac', fps=24)
background_clip = VideoFileClip("background_image_video.mp4")
# Concatenate enough times to exceed final video length
background_clip = concatenate_videoclips([background_clip] * 20)
background_audio = AudioFileClip("AcousticGuitar1.mp3")

countdown_video_import = VideoFileClip("countdown-5min.mp4")



#amazon Polly settings

# Set constants
screen_width = 1920
screen_height = 1080
font = 'Lucida Grande'
intro_clip_duration = 5
#question clip is set to the length of audio + 2 seconds
transition_duration = 2

#set video file name to include date and time
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
name, extension = original_filename.rsplit('.', 1)
new_filename = f"{name}-{current_datetime}.{extension}"
question_options_width = 800

#folder name for audio files and images.
folder_name = name #from final video filename.
# Ensure the folder exists
os.makedirs(folder_name, exist_ok=True)

# Colors
intro_clip_text_background = (93, 115, 126)
questions_box_background = (93, 115, 126)
question_number_color = '#FFCC99'
question_number_color_background = '#55505C'
question_background = '#FFCC99'
questions_text_color = '#55505C'
questions_text_color_background = '#FFCC99'
black_text = '#55505C'
letter_clip_background = "#5D737E"
question_box_background = '#55505C'

# For questions in quiz
text_clip_width = 600
text_clip_height = 70
gap_height = 0
total_vertical_space = 4 * text_clip_height
top_margin = (screen_height - total_vertical_space) / 2

# Format imports
background_clip = background_clip.fx(vfx.speedx, 0.30)
background_clip = background_clip.set_fps(30)

# Ensure ImageMagick is set correctly
os.environ["IMAGEMAGICK_BINARY"] = "/usr/local/bin/convert"  # Path to ImageMagick binary


def print_memory_usage():
    process = psutil.Process(os.getpid())
    print(f"Memory usage: {process.memory_info().rss / 1024 ** 2} MB")


# Initialize the Polly client
polly = boto3.client('polly')

# Set the dimensions of the final clip
width, height = 1920, 1080


# Text-to-speech function
def generate_text_to_speech(index, text, amazon_voice_name, amazon_voice_engine):
    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=amazon_voice_name,
            Engine=amazon_voice_engine
        )
    except (BotoCoreError, ClientError) as error:
        print(error)
        sys.exit(-1)

    if 'AudioStream' in response:
        audio_path = os.path.join(folder_name, f"{index}.mp3")
        with open(audio_path, 'wb') as file:
            file.write(response['AudioStream'].read())
            print(file.name)
            return file.name
        print("The audio file has been saved as hello_world.mp3")
    else:
        print("Could not stream audio from AWS Polly")

# MODIFIED: Resize the smaller video to 200x356 pixels and adjust duration
#countdown_video = countdown_video_import.resize(height=200)
#countdown_video_duration = countdown_video.duration


# Create an empty list to store video clips
video_clips = []

# Create an intro clip
intro_text_audio = generate_text_to_speech("intro_text_audio", quiz_name, "Ruth", "long-form")

intro_clip = TextClip(txt=quiz_name, color='white', font=font, fontsize=70).set_duration(intro_clip_duration)
intro_clip = intro_clip.set_position(('center', 'center'))
intro_clip_size = intro_clip.size

intro_clip_shadow = TextClip(txt=quiz_name, color='black', font=font, fontsize=70).set_duration(intro_clip_duration).set_position(
    lambda t: (intro_clip.size[0]/2 - intro_clip.size[0]/2 + 24,
               intro_clip.size[1]/2 - intro_clip.size[1]/2 + 16)
)
intro_width, intro_height = intro_clip.size

intro_clip_background = ColorClip(size=(intro_width + 40, intro_height + 20), color=intro_clip_text_background, duration=intro_clip_duration).set_position(('center', 'center'))
intro_clip_background = intro_clip_background.set_opacity(0.8)

intro_clip_video = CompositeVideoClip([intro_clip_background, intro_clip_shadow, intro_clip])
intro_clip_video = intro_clip_video.set_position(('center', 'center'))
intro_clip_video = CompositeVideoClip([ColorClip(size=(width, height), color=(0,0,0,0)).set_duration(5)] + [intro_clip_video], size=(width, height))

intro_audio_clip = AudioFileClip(f"{folder_name}/intro_text_audio.mp3")
intro_clip_video = intro_clip_video.set_audio(intro_audio_clip)

video_clips.append(intro_clip_video)
#intro_clip_video.preview()

#countdown_video_import_subclip = countdown_video_import.subclip((countdown_video_import.duration - intro_audio_clip.duration), countdown_video_import.duration)
#countdown_video_import_subclip.preview()
# Create title for question slides
def create_title_clip(duration, text):
    title_clip = TextClip(txt=text, color='white', font=font, fontsize=50).set_duration(duration)
    title_width, title_height = title_clip.size
    title_clip_shadow = TextClip(txt=text, color='black', font=font, fontsize=50).set_duration(duration).set_position(
        lambda t: (title_clip.size[0]/2 - title_clip.size[0]/2 + 23,
                   title_clip.size[1]/2 - title_clip.size[1]/2 + 14)
    )

    title_clip_background = ColorClip(size=(title_width + 40, title_height + 20), color=intro_clip_text_background, duration=duration)
    title_clip_background = title_clip_background.set_opacity(0.8)

    title_clip_video = CompositeVideoClip([title_clip_background.set_position(('center', 'center')), title_clip_shadow, title_clip.set_position('center', 'center')])
    title_clip_video = title_clip_video.set_position(('center', 20))

    return title_clip_video


# Process each question in the quiz data

def create_question_clips(answers, question_audio_clip, top_margin, text_clip_height, gap_height, font, question_options_width, black_text, question_background):
    for i, text in enumerate(answers):
        question_clip = TextClip(text, fontsize=45, font=font, color=black_text, bg_color='#F6F6F6', method='caption', size=(question_options_width, None))
        question_clip = question_clip.margin(left=40, right=40, top=10, bottom=10)
        top_position = top_margin + i * (text_clip_height + gap_height)
        question_clip = question_clip.set_position((1000, top_position))
        question_clip = question_clip.set_audio(question_audio_clip)
        yield question_clip


for index, row in quiz_data.iterrows():
    question = row['Response']

    question_number = TextClip(str(index+1), fontsize=40, font=font, color=questions_text_color, stroke_width=4, bg_color=questions_text_color_background, method='caption', size=(80, None))
    question_number = question_number.set_position((20, 20))
    amazon_voice_name = row['VoiceName']
    amazon_voice_engine = row['amazon_voice_engine']

    question_audio = generate_text_to_speech(f"question_for_{index+1}", row['Response'],amazon_voice_name, amazon_voice_engine)
    question_audio_clip = AudioFileClip(f"{folder_name}/question_for_{index+1}.mp3")

    countdown_video_for_questions = countdown_video_import.resize(height=200)
    countdown_video_for_questions_duration = question_audio_clip.duration + 2
    subclip_start = countdown_video_import.duration - countdown_video_for_questions_duration
    countdown_video_for_questions = countdown_video_for_questions.subclip(subclip_start, countdown_video_import.duration)
    countdown_video_for_questions = countdown_video_for_questions.set_position((screen_width - 356, screen_height - 200))

    video = ColorClip(size=(screen_width, screen_height), color=(0, 0, 0, 0), duration=(question_audio_clip.duration + 4))

    question_name = TextClip(question, fontsize=60, font=font, color=black_text, stroke_width=4, bg_color=question_background, method='caption', size=(1200, None))
    question_name = question_name.set_position(('center', 200))

    title_clip_video = create_title_clip(countdown_video_for_questions_duration, quiz_name)

    bullets_video = CompositeVideoClip([video, title_clip_video, question_name, countdown_video_for_questions, question_number])

    # MODIFIED: Updated durations
    bullets_video.duration = question_audio_clip.duration + 2
    bullets_video = bullets_video.fadein(1)
    bullets_video = bullets_video.set_audio(question_audio_clip)

    # MODIFIED: Updated start times
    bullets_video = bullets_video.set_start(5 + index * 10)

    video_clips.extend([bullets_video])


# Create an intro clip
outro_text = "Thanks for playing!\n\nDon't forget to like and subscribe."
outro_text_audio = generate_text_to_speech("outro_text_audio", outro_text, "Ruth", "long-form")

outro_clip = TextClip(txt=outro_text, color='white', font=font, fontsize=70).set_duration(intro_clip_duration)
outro_clip = outro_clip.set_position(('center', 'center'))
outro_clip_size = outro_clip.size

outro_clip_shadow = TextClip(txt=outro_text, color='black', font=font, fontsize=70).set_duration(intro_clip_duration).set_position(
    lambda t: (outro_clip.size[0]/2 - outro_clip.size[0]/2 + 24,
               outro_clip.size[1]/2 - outro_clip.size[1]/2 + 16)
)
outro_width, outro_height = outro_clip.size

outro_clip_background = ColorClip(size=(outro_width + 40, outro_height + 20), color=intro_clip_text_background, duration=intro_clip_duration).set_position(('center', 'center'))
outro_clip_background = outro_clip_background.set_opacity(0.8)

outro_clip_video = CompositeVideoClip([outro_clip_background, outro_clip_shadow, outro_clip])
outro_clip_video = outro_clip_video.set_position(('center', 'center'))
outro_clip_video = CompositeVideoClip([ColorClip(size=(width, height), color=(0,0,0,0)).set_duration(5)] + [outro_clip_video], size=(width, height))

outro_audio_clip = AudioFileClip("outro_text_audio.mp3")

# Calculate the total duration of all video clips (excluding the outro for now)
total_duration = sum(clip.duration for clip in video_clips)

# Set the start time for the outro clip
outro_clip_video = outro_clip_video.set_start(total_duration)
outro_clip_video = outro_clip_video.set_audio(outro_audio_clip.set_start(total_duration))
print(f"Outro video duration: {outro_clip_video.duration}")


# Append the outro clip to the list of video clips
video_clips.append(outro_clip_video)
#outro_clip_video.preview()

# Update the background clip duration to match the total duration of all clips
total_video_duration = total_duration + outro_clip_video.duration
print(total_video_duration)

# Calculate the total video duration
total_video_duration = sum(clip.duration for clip in video_clips)

# Loop the background audio and adjust its volume
background_audio = afx.audio_loop(background_audio, duration=total_video_duration)
background_audio = background_audio.volumex(0.2)

# Loop the background video to match the total video duration
looped_background = background_clip.fx(vfx.loop, duration=total_video_duration)

# Concatenate all the video clips into a single video
final_clip = concatenate_videoclips(video_clips)

# Combine the background audio with the final clip's audio
final_audio = CompositeAudioClip([final_clip.audio, background_audio.set_duration(final_clip.duration).volumex(0.1)])
final_clip = final_clip.set_audio(final_audio)

# Create the final composite video with the looped background
final_composite = CompositeVideoClip([looped_background, final_clip])

# Write the final video to a file
final_composite.write_videofile(new_filename, codec='libx264', audio_codec='aac', fps=24)

print(f"Video saved as {new_filename}")
