'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import re

audio_dir= "audio/"
audio_file = "Ren-ai.m4a"
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
    def __init__(self, index, start, text):
        super().__init__()
        self.index = index
        self.start = start
        self.text = text
        #self.main = main()
    
    def build(self):
        self.display_start = ft.Text(f"{self.start} (ms)")
        self.display_text= ft.TextButton(text=f"{self.text}", on_click=self.edit_clicked, tooltip='Click to edit')
        self.edit_text = ft.TextField(expand=1)

        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.display_start,
                self.display_text,
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            ft.icons.PLAY_ARROW_OUTLINED,
                            tooltip='Play Here'
                            #on_click=self.jump_clicked,
                        )
                    ]
                )
            ]
        )
        self.edit_view = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.edit_text,
                ft.IconButton(
                    icon=ft.icons.DONE_OUTLINE_OUTLINED,
                    tooltip='Update Text',
                    on_click=self.save_clicked,
                ),
                ft.IconButton(
                    icon=ft.icons.CANCEL_OUTLINED,
                    tooltip='Close wihout change',
                    on_click=self.cancel_clicked,
                )
            ]
        )
        return ft.Column(controls=[self.display_view, self.edit_view])

    def edit_clicked(self, e):
        self.edit_text.value = self.display_text.text
        self.display_view.visible = False
        self.edit_view.visible = True
        #self.main.play_button_clicked()
        self.update()

    def save_clicked(self, e):
        self.display_text.text= self.edit_text.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()

    def cancel_clicked(self, e):
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()

    def jump_clicked(self, e):
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
            index = page.subtitles[i][0]
            start_time = page.subtitles[i][1]
            text = page.subtitles[i][2]
            # Create instance
            sub = SubButton(index, start_time, text)
            subs_view.controls.append(sub)
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
        page.position = audio1.get_current_position()
        #print("Position:", page.position)
        if (page.isPlaying == False) and (page.position == 0):
            audio1.play()
            page.isPlaying = True
            play_button.icon=ft.icons.PAUSE
            play_button.text = "Playing"
        elif page.isPlaying == False:
            audio1.resume()
            page.isPlaying = True
            play_button.icon=ft.icons.PAUSE
            play_button.text = "Playing"
        else:
            audio1.pause()
            page.isPlaying = False
            play_button.icon=ft.icons.PLAY_ARROW
            play_button.text = "Paused"
        page.update()
    
    def playback_completed(e):
        if e.data == "completed":
            page.isPlaying = False 
            play_button.icon=ft.icons.PLAY_ARROW
            play_button.text = "Play"
        page.update()
    
    def rewind_clicked(e):
        if audio_slider.value <= 5*1000:
            audio_slider.value = 0
        else:
            audio_slider.value -= 5*1000
        audio1.seek(int(audio_slider.value))
        print(int(audio_slider.value))
        page.update()

    audio_slider = ft.Slider(
        min = 0,
        value = int(page.position/10000),
        label = "{value}ms",
        on_change = slider_changed,
    )

    play_button = ft.ElevatedButton(
        icon=ft.icons.PLAY_ARROW,
        text = "Play",
        autofocus=True,
        on_click=play_button_clicked
    )

    position_text = ft.Text(value=audio_slider.value)
    duration_text = ft.Text(value=page.duration)
    
    subs_view = ft.Column(
        spacing = 10,
        width = float("inf"),
        scroll = ft.ScrollMode.ALWAYS,
    )
    
    rewind_button = ft.ElevatedButton(
        icon=ft.icons.FAST_REWIND,
        text="5 secs",
        tooltip='Rewind 5 secs',
        on_click=rewind_clicked,
    )
    
    audio1 = ft.Audio(
        src=audio_dir+audio_file,
        volume=1,
        balance=0,
        on_loaded=loaded,
        on_position_changed = position_changed,
        on_state_changed = playback_completed,
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
            rewind_button,
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