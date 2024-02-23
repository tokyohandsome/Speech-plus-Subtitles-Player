'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import re

audio_dir= "audio/"
#audio_file = "Ren-ai.m4a"
audio_file = "Ochiai.mp3"
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
    def __init__(self, index, start_time, text, sub_time_clicked):
        super().__init__()
        self.index = index
        self.start_time = start_time
        self.text = text
        self.sub_time_clicked = sub_time_clicked
        #self.main = main()
    
    def build(self):
        self.display_start_time = ft.TextButton(text=f"{self.start_time} (ms)",
                                           tooltip="Click to jump",
                                           on_click=self.jump_clicked,)
        self.display_text= ft.TextButton(text=f"{self.text}", 
                                         on_click=self.edit_clicked, 
                                         tooltip='Click to edit')
        self.edit_text = ft.TextField(expand=1)

        self.display_view = ft.Row(
            #alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.display_start_time,
                self.display_text,
                #ft.Row(spacing=0, controls=[ft.IconButton(ft.icons.PLAY_ARROW_OUTLINED,)])
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
        self.sub_time_clicked(self.start_time)

class AudioSubPlayer(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.position = 0
        self.duration = 0
        self.isPlaying = False

        self.audio_slider = ft.Slider(
            min = 0,
            value = int(self.position/10000),
            label = "{value}ms",
            on_change = self.slider_changed,
        )

        self.play_button = ft.ElevatedButton(
            icon=ft.icons.PLAY_ARROW,
            text = "Play",
            autofocus=True,
            on_click=self.play_button_clicked
        )

        self.position_text = ft.Text(value=self.audio_slider.value)
        self.duration_text = ft.Text(value=self.duration)
        
        self.subs_view = ft.Column(
            spacing = 5,
            height= 300,
            #expand=True,
            width = float("inf"),
            scroll = ft.ScrollMode.ALWAYS,
        )
        
        self.rewind_button = ft.ElevatedButton(
            icon=ft.icons.FAST_REWIND,
            text="5 secs",
            tooltip='Rewind 5 secs',
            on_click=self.rewind_clicked,
        )
        
        self.audio1 = ft.Audio(
            src=audio_dir+audio_file,
            volume=1,
            balance=0,
            on_loaded=self.loaded,
            on_position_changed = self.position_changed,
            on_state_changed = self.playback_completed,
        )

    def loaded(self, e):
        #print("Loaded")
        self.audio_slider.max = self.audio1.get_duration()
        self.duration_text.value = self.audio_slider.max
        #print("audio_slider.max:", self.audio_slider.max)
        self.audio_slider.divisions = self.audio_slider.max//60
        self.subtitles = create_subtitles("assets/"+srt_dir+srt_file)
        print(self.subtitles)
        #print(type(self.subtitles))

        # Extract subtitles as buttons
        print("Extract subtitles as buttons.")
        for i in range(len(self.subtitles)):
            index = self.subtitles[i][0]
            start_time = self.subtitles[i][1]
            text = self.subtitles[i][2]
            sub_time = ''
            # Create instance
            sub = SubButton(index, start_time, text, self.sub_time_clicked)
            self.subs_view.controls.append(sub)
        self.update()

    def position_changed(self, e):
        self.audio_slider.value = e.data
        print("Position:", self.audio_slider.value)
        self.position_text.value = e.data
        self.update()

    def slider_changed(self, e):
        self.audio1.seek(int(self.audio_slider.value))
        print(int(self.audio_slider.value))
        self.update()

    def play_button_clicked(self, e):
        self.position = self.audio1.get_current_position()
        #print("Position:", page.position)
        if (self.isPlaying == False) and (self.position == 0):
            self.audio1.play()
            self.isPlaying = True
            self.play_button.icon=ft.icons.PAUSE
            self.play_button.text = "Playing"
        elif self.isPlaying == False:
            self.audio1.resume()
            self.isPlaying = True
            self.play_button.icon=ft.icons.PAUSE
            self.play_button.text = "Playing"
        else:
            self.audio1.pause()
            self.isPlaying = False
            self.play_button.icon=ft.icons.PLAY_ARROW
            self.play_button.text = "Paused"
        self.update()
    
    def playback_completed(self, e):
        if e.data == "completed":
            self.isPlaying = False 
            self.play_button.icon=ft.icons.PLAY_ARROW
            self.play_button.text = "Play"
        self.update()
    
    def rewind_clicked(self, e):
        if self.audio_slider.value <= 5*1000:
            self.audio_slider.value = 0
        else:
            self.audio_slider.value -= 5*1000
        self.audio1.seek(int(self.audio_slider.value))
        print(int(self.audio_slider.value))
        self.update()

    def sub_time_clicked(self, start_time):
        self.audio1.seek(int(start_time))
        self.update

    # *** BUILD METHOD ***
    def build(self):
        self.view = ft.Container(content=ft.Column([
                ft.Text(value=f"Base Directories: assets/audio and assets/text"),
                ft.Text(value=f"Audio File: {audio_file}"),
                ft.Text(value=f"Text File: {srt_file}"),
                self.audio_slider,
                ft.Row([
                    ft.Text(value="0"),
                    self.position_text,
                    self.duration_text,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row(controls=[
                    self.rewind_button,
                    self.play_button,
                    ft.ElevatedButton(
                        "Get current position",
                        on_click=lambda _: print("Current position:", self.audio1.get_current_position()),
                    )
                    ]),
                    ft.Container(self.subs_view, 
                                 border=ft.border.all(1), 
                                 #expand=False, 
                                 ),
                ],
            ),
        )
        return self.view

def main(page: ft.Page):
    page.title = 'Audio + Subtitle Player'
    page.update()

    app = AudioSubPlayer()
    
    page.add(app)
    print("Page added.")
    page.overlay.append(app.audio1)
    page.update()


ft.app(target=main, assets_dir="assets")
#ft.app(target=main)