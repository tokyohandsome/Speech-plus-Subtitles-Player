'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import re

audio_dir= "audio/"
audio_file = "Ochiai.mp3"
#audio_file = "YoroTakeshi.m4a"
#audio_file = "YoroTakeshi.m4a"
srt_dir = "text/"
srt_file = os.path.splitext(os.path.basename(audio_file))[0]+".txt"
print(srt_dir+srt_file)
if srt_dir+srt_file:
    print("File exists.")

# Create a list from text file.
# subs[n] = [index_number: str, start_time: str, text: str]
def create_subtitles(file):
    subs = []
    sub = []
    counter = 0
    with open(file, 'r') as h:
        for line in h.readlines():
            # Remove '\n' at the end of each line.
            line = line.rstrip()
            if counter % 3 == 0:
                sub = sub + [line]
                counter += 1
            elif counter % 3 == 1:
                sub = sub + [line.zfill(8)]
                counter += 1
            else:
                sub = sub + [line]
                subs.append(sub)
                sub = []
                counter += 1
    return(subs)

class SubButton(ft.UserControl):
    def build(self):
        pass

def main(page: ft.Page):
    page.title = 'Audio + Subtitle Player'
    page.isPlaying = False
    page.position = 0
    page.duration = 0
    #page.scroll = "adaptive"

    def loaded(e):
        print("Loaded")
        audio_slider.max = audio1.get_duration()
        duration_text.value = audio_slider.max
        print("audio_slider.max:", audio_slider.max)
        audio_slider.divisions = audio_slider.max//60
        page.subtitles = create_subtitles("assets/"+srt_dir+srt_file)
        print(page.subtitles)
        print(type(page.subtitles))

        # Extract subtitles as buttons
        print("Extract subtitles as buttons.")
        for i in range(len(page.subtitles)):
            key_num = page.subtitles[i][0]
            start_time = page.subtitles[i][1]
            text = page.subtitles[i][2]
            subs_view.controls.append(
                ft.TextButton(
                        content=ft.Text(
                            f"[{start_time}] {text}", 
                            text_align=ft.CrossAxisAlignment.START, 
                            expand=True
                            ),
                        #width = float("inf"),
                        key=key_num,
                        #on_long_press=jump(key_num, start_time),
                        on_click=jump(key_num, start_time),
                ), 
            )
        page.update()

    def jump(key, start):
        #jump_to = str(int(e.data))
        #audio_slider.value = jump_to
        #print("Jump to:", e)
        #print(f"Key: {key}, Start: {start}")
        #print("Button cliecked")
        page.update()

    def position_changed(e):
        audio_slider.value = e.data
        print("Position:", audio_slider.value)
        position_text.value = e.data
        page.update()

    def slider_changed(e):
        audio1.seek(int(audio_slider.value))
        print(int(audio_slider.value))
        page.update()

    def play_button_clicked(e):
        #print("Playing?", page.isPlaying)
        page.position = audio1.get_current_position()
        #print("Position:", page.position)
        if (page.isPlaying == False) and (page.position == 0):
            audio1.play()
            page.isPlaying = True
            play_button.text = "Playing"
        elif page.isPlaying == False:
            audio1.resume()
            page.isPlaying = True
            play_button.text = "Playing"
        else:
            audio1.pause()
            page.isPlaying = False
            play_button.text = "Paused"
        page.update()
    
    def playback_completed(e):
        if e.data == "completed":
            page.isPlaying = False 
            play_button.text = "Play"
        page.update()

    audio_slider = ft.Slider(
        min = 0,
        value = int(page.position/10000),
        label = "{value}ms",
        on_change = slider_changed,
    )

    play_button = ft.ElevatedButton(
        text = "Play",
        autofocus=True,
        #on_click=play_button_clicked(isPlaying)
        on_click=play_button_clicked
    )

    position_text = ft.Text(value=audio_slider.value)
    duration_text = ft.Text(value=page.duration)
    
    subs_view = ft.Column(
        spacing = 10,
        width = float("inf"),
        #alignment = ft.CrossAxisAlignment.START,
        scroll = ft.ScrollMode.ALWAYS,
    )
    
    audio1 = ft.Audio(
        src=audio_dir+audio_file,
        #autoplay = True,
        volume=1,
        balance=0,
        on_loaded=loaded,
        on_position_changed = position_changed,
        #on_state_changed=lambda e: isPlaying=e.data,
        on_state_changed = playback_completed,
        #on_state_changed=play_button_clicked,
        #on_seek_complete=lambda _: print("Seek complete"),
    )
    page.overlay.append(audio1)        

    page.add(
        ft.Text(value=f"Base Directories: assets/audio and assets/text"),
        ft.Text(value=f"Audio File: {audio_file}"),
        ft.Text(value=f"Text File: {srt_file}"),
        audio_slider,
        ft.Row(controls=[
            ft.Text(value="0"),
            position_text,
            duration_text,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Row(controls=[
            play_button,
            ft.ElevatedButton(
                "Get current position",
                on_click=lambda _: print("Current position:", audio1.get_current_position()),
            )
            ]),
        ft.Container(
            subs_view, border=ft.border.all(1), 
            expand=True,
            ),
        ),
    

ft.app(target=main, assets_dir="assets")
#ft.app(target=main)