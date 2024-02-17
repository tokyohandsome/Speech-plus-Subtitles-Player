'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import re

url = "https://github.com/mdn/webaudio-examples/blob/main/audio-analyser/viper.mp3?raw=true"
audio_dir= "audio/"
#audio_file = "Ochiai.mp3"
#audio_file = "YoroTakeshi.m4a"
audio_file = "YoroTakeshi.m4a"
srt_dir = "text/"
srt_file = os.path.splitext(os.path.basename(audio_file))[0]+".txt"
print(srt_dir+srt_file)
if srt_dir+srt_file:
    print("File exists.")

# Create tables from text file.
# subs[n] = [index_number: str, start_time: str, text: str]
def create_subtitles(file):
    subs = []
    sub = []
    counter = 0
    with open(file, 'r') as h:
        for line in h.readlines():
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

def main(page: ft.Page):
    page.isPlaying = False
    page.position = 0
    page.subtitles = ''
    #page.scroll = "adaptive"

    '''
    # Page theme copied from Scrolling column programmatically page
    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(
            track_color={
                ft.MaterialState.HOVERED: ft.colors.AMBER,
                ft.MaterialState.DEFAULT: ft.colors.TRANSPARENT,
            },
            track_visibility=True,
            track_border_color=ft.colors.BLUE,
            thumb_visibility=True,
            thumb_color={
                ft.MaterialState.HOVERED: ft.colors.RED,
                ft.MaterialState.DEFAULT: ft.colors.GREY_300,
            },
            thickness=30,
            radius=15,
            main_axis_margin=5,
            cross_axis_margin=10,
            # interactive=False,
        )
    )
    '''
    def loaded(e):
        print("Loaded")
        audio_slider.max = audio1.get_duration()
        #audio_slider.label = audio1.get_current_position()
        print("Duration:", audio_slider.max)
        audio_slider.divisions = audio_slider.max//60
        page.subtitles = create_subtitles("assets/"+srt_dir+srt_file)
        print(page.subtitles)
        page.update()

    def position_changed(e):
        audio_slider.value = e.data
        print("Position:", audio_slider.value)
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

    def add_list(e):
        print("Adding list items.")
        for i in range(len(page.subtitles)):
            #print(page.subtitles[i])
            #key_num = int(page.subtitles[i][0])
            start_time = page.subtitles[i][1]
            text = page.subtitles[i][2]
            cl.controls.append(ft.Text(f"[{start_time}] {text}"))
        page.update()

    audio1 = ft.Audio(
        src=audio_dir+audio_file,
        #autoplay = True,
        volume=1,
        balance=0,
        on_loaded=loaded,
        on_position_changed = position_changed,
        #on_state_changed=lambda e: isPlaying=e.data,
        #on_state_changed=play_button_clicked,
        on_seek_complete=lambda _: print("Seek complete"),
    )
    page.overlay.append(audio1)
    
    audio_slider = ft.Slider(
        min = 0,
        value = int(page.position/10000),
        label = "{value}ms",
        on_change = slider_changed,
    )

    play_button = ft.ElevatedButton(
        text = "Play",
        #on_click=play_button_clicked(isPlaying)
        on_click=play_button_clicked
    )

    position_duration = ft.Row([
        ft.Text(value=audio_slider.value, 
                #text_align=ft.TextAlign.LEFT
                ),
        ft.Text(value=audio_slider.max, 
                #text_align=ft.TextAlign.RIGHT
                ),
    ], #alignment=ft.MainAxisAlignment.SPACE_EVENLY,
    )
    
    cl = ft.Column(
        spacing = 10,
        height = 200,
        width = float("inf"),
        scroll = ft.ScrollMode.ALWAYS,
    )
        
    page.add(
        ft.Text(value=f"Base Directories: assets/audio and assets/text"),
        ft.Text(value=f"Audio File: {audio_file}"),
        ft.Text(value=f"Text File: {srt_file}"),
        audio_slider,
        position_duration,
        ft.Row([
            play_button,
            ft.ElevatedButton(
                "Get current position",
                on_click=lambda _: print("Current position:", audio1.get_current_position()),
            )
            ]),
        ft.Container(cl, border=ft.border.all(1)),
        ft.TextButton(text="import list", on_click=add_list),
        ),
    

ft.app(target=main, assets_dir="assets")
#ft.app(target=main)