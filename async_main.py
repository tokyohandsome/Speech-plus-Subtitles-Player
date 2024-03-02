'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import numpy as np

speech_dir= "speech/"
speech_file = ''
#speech_file = "Ren-ai.m4a"
#speech_file = "Ochiai.mp3"
speech_file = "YoroTakeshi.m4a"
#speech_file = "ukrain.m4a"
#speech_file = "pivot.m4a"
srt_dir = "text/"
srt_file = ''
if speech_file != '':
    srt_file = os.path.splitext(os.path.basename(speech_file))[0]+".txt"
    print(srt_dir+srt_file)
if srt_dir+srt_file:
    print("File exists.")

# Create a list from text file.
# subs[n] = [index_number: str, start_time: str, end_time: str, text: str]
def create_subtitles(file):
    subs = []
    sub = []
    counter = 0
    with open(file, 'r') as h:
        for line in h.readlines():
            # Remove '\n' at the end of each line.
            line = line.rstrip()
            if counter % 4 == 0:
                # Index
                sub = sub + [line]
                counter += 1
            elif counter % 4 == 1:
                # Start time
                sub = sub + [line.zfill(8)]
                counter += 1
            elif counter % 4 == 2:
                # End time
                sub = sub + [int(line)]
                counter += 1
            else:
                # Text
                sub = sub + [line]
                subs.append(sub)
                sub = []
                counter += 1
    return(subs)

class SubButton(ft.UserControl):
    def __init__(self, index, start_time, end_time, text, sub_time_clicked, play_button):
        super().__init__()
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.sub_time_clicked = sub_time_clicked
        self.play_button = play_button
    
    def build(self):
        self.display_start_time = ft.TextButton(text=f"{self.start_time} (ms)",
                                           tooltip="Click to jump",
                                           key=self.index,
                                           on_click=self.jump_clicked,)
        self.display_text= ft.TextButton(text=f"{self.text}", 
                                         on_click=self.edit_clicked, 
                                         tooltip='Click to edit')
        self.edit_text = ft.TextField(expand=1)

        self.display_view = ft.Row(
            #alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            alignment=ft.MainAxisAlignment.START,
            #vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                #ft.Text(value=self.index),
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

    async def edit_clicked(self, e):
        self.edit_text.value = self.display_text.text
        await self.edit_text.focus_async()
        self.display_view.visible = False
        self.edit_view.visible = True
        self.edit_text.on_submit = self.save_clicked
        await self.update_async()

    async def save_clicked(self, e):
        self.display_text.text= self.edit_text.value
        self.display_view.visible = True
        self.edit_view.visible = False
        await self.play_button.focus_async()
        await self.update_async()

    async def cancel_clicked(self, e):
        self.display_view.visible = True
        self.edit_view.visible = False
        await self.play_button.focus_async()
        await self.update_async()

    async def jump_clicked(self, e):
        await self.sub_time_clicked(self.start_time)

class AudioSubPlayer(ft.UserControl):
    def __init__(self, speech_dir, speech_file, srt_dir, srt_file):
        super().__init__()
        self.position = 0
        self.duration = 0
        self.isPlaying = False
        self.speech_dir = speech_dir
        self.speech_file = speech_file
        self.srt_dir = srt_dir
        self.srt_file = srt_file

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
            height= 400,
            #expand=True,
            width = float("inf"),
            scroll = ft.ScrollMode.ALWAYS,
            auto_scroll=False,
        )
        
        self.rewind_button = ft.ElevatedButton(
            icon=ft.icons.FAST_REWIND,
            text="5 secs",
            tooltip='Rewind 5 secs',
            on_click=self.rewind_clicked,
        )

        self.sub_scroller_sw = ft.Switch(
            label='Auto scroll',
            value=True,
        )
        
        self.audio1 = ft.Audio(
            src=self.speech_dir+self.speech_file,
            volume=1,
            balance=0,
            on_loaded=self.loaded,
            on_position_changed = self.position_changed,
            on_state_changed = self.playback_completed,
        )

        #self.pick_files_dialog = ft.FilePicker(on_result=self.pick_speech_file_result)
        #self.selected_files = ft.Text()

        self.save_file_dialog = ft.FilePicker(on_result=self.save_file_result)
        self.save_file_path = ft.Text()

        self.speech_file_button = ft.ElevatedButton(
            text='Speech File', 
            icon=ft.icons.MUSIC_NOTE, 
            on_click=self.pick_speech_file,
        )

        self.pick_speech_file_dialog = ft.FilePicker(on_result=self.pick_speech_file_result)

        self.speech_file_name = ft.Text(value=f"{self.speech_file}")

    async def loaded(self, e):
        #print("Loaded")
        #await self.audio1.get_duration_async()
        #print(f'type of get_duration_async() = {type(self.audio1.get_duration_async)}')
        self.audio_slider.max = int(await self.audio1.get_duration_async())
        #print(f'type(self.audio_slider.max) = {type(self.audio_slider.max)}')
        self.duration_text.value = self.audio_slider.max
        #print("audio_slider.max:", self.audio_slider.max)
        self.audio_slider.divisions = self.audio_slider.max//60
        #self.audio_slider.divisions = round(self.audio_slider.max/60)
        self.subtitles = create_subtitles("assets/"+srt_dir+srt_file)
        #print(self.subtitles)
        #print(type(self.subtitles))

        # Extract subtitles as buttons
        #print("Extract subtitles as buttons.")
        for i in range(len(self.subtitles)):
            index = self.subtitles[i][0]
            start_time = self.subtitles[i][1]
            end_time = self.subtitles[i][2]
            text = self.subtitles[i][3]
            # Create instance
            sub = SubButton(index, start_time, end_time, text, self.sub_time_clicked, self.play_button)
            self.subs_view.controls.append(sub)
        await self.update_async()

    async def position_changed(self, e):
        self.audio_slider.value = e.data
        print("Position:", self.audio_slider.value)
        self.position_text.value = e.data
        if self.sub_scroller_sw.value == True:
            await self.scroll_to(self.audio_slider.value)
        await self.update_async()

    async def slider_changed(self, e):
        await self.audio1.seek_async(int(self.audio_slider.value))
        print(int(self.audio_slider.value))
        await self.update_async()

    async def play_button_clicked(self, e):
        self.position = await self.audio1.get_current_position_async()
        #print("Position:", page.position)
        if (self.isPlaying == False) and (self.position == 0):
            await self.audio1.play_async()
            self.isPlaying = True
            self.play_button.icon=ft.icons.PAUSE
            self.play_button.text = "Playing"
        elif self.isPlaying == False:
            await self.audio1.resume_async()
            self.isPlaying = True
            self.play_button.icon=ft.icons.PAUSE
            self.play_button.text = "Playing"
        else:
            await self.audio1.pause_async()
            self.isPlaying = False
            self.play_button.icon=ft.icons.PLAY_ARROW
            self.play_button.text = "Paused"
        await self.update_async()
    
    async def playback_completed(self, e):
        if e.data == "completed":
            self.isPlaying = False 
            self.play_button.icon=ft.icons.PLAY_ARROW
            self.play_button.text = "Play"
        await self.update_async()
    
    async def rewind_clicked(self, e):
        if self.audio_slider.value <= 5*1000:
            self.audio_slider.value = 0
        else:
            self.audio_slider.value -= 5*1000
        await self.audio1.seek_async(int(self.audio_slider.value))
        print(int(self.audio_slider.value))
        await self.update_async()

    async def sub_time_clicked(self, start_time):
        await self.audio1.seek_async(int(start_time))
        await self.update_async()
    
    async def scroll_to(self, e):
        end_time = [item[2] for item in self.subtitles]
        index = np.argmin(np.abs(np.array(end_time) - e))
        key=str(self.subtitles[index][0])
        #print(f"e= {e}")
        #print(f"index= {index}", f"type = {type(index)}")
        #print(f'key={key}')
        #await self.subs_view.scroll_to_async(key=key, duration=2000)
        await self.subs_view.scroll_to_async(key=key, duration =1000)
        await self.update_async()
    
    async def pick_speech_file(self, e):
        await self.pick_speech_file_dialog.pick_files_async(
            dialog_title='Select a SPEECH (audio) file',
            allow_multiple=False,
        )

    async def pick_speech_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            print(f'e.files = {e.files}')
            #print(f'type(e.files) = {type(e.files)}')
            self.speech_file = ''.join(map(lambda f: f.name, e.files))
            print(f'File name= {self.speech_file}')
            self.speech_dir = os.path.dirname(''.join(map(lambda f: f.path, e.files)))+'/'
            print(f'Full path= {self.speech_dir}')
            #await self.speech_file_name.update_async()
            await self.audio1.update_async()
            await self.update_async()

    # Save file dialog
    async def save_file_result(self, e: ft.FilePickerResultEvent):
        self.save_file_path.value = e.path if e.path else "Cancelled!"
        await self.save_file_path.update()

    # *** BUILD METHOD ***
    def build(self):
        self.view = ft.Column(expand=True, controls=[
            ft.Container(content=
                ft.Column(controls=[
                    ft.Row(controls=[
                        ft.Text(value=f"Base Directories: assets/audio and assets/text"),
                    ]),
                    ft.Row(controls=[
                        self.speech_file_button,
                        #ft.Text(value=f"{self.speech_file}"),
                        self.speech_file_name,
                    ]),
                    ft.Row(controls=[
                        ft.ElevatedButton(text='Text/SRT File', icon=ft.icons.TEXT_SNIPPET_OUTLINED),
                        ft.Text(value=f"{srt_file}"),
                        ft.ElevatedButton(text='Save', icon=ft.icons.SAVE_OUTLINED, tooltip='Update current Text/SRT file'),
                        ft.ElevatedButton(text='Export as...', icon=ft.icons.SAVE_ALT),
                    ]),
                    self.audio_slider,
                    ft.Row([
                        ft.Text(value="0"),
                        self.position_text,
                        self.duration_text,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row(controls=[
                        self.rewind_button,
                        self.play_button,
                        self.sub_scroller_sw,
                        ft.ElevatedButton(
                            "Get current position",
                            on_click=lambda _: print("Current position:", self.audio1.get_current_position()),
                        )
                    ]),
                ]), expand=False, border_radius=10, border=ft.border.all(1), padding=10, 
            ),
            ft.Container(content=
                self.subs_view,
                border_radius=10,
                border=ft.border.all(1),
                #expand=False,
                padding=5,
            )
            ])
        
        #return ft.Column(expand=True, controls=self.view)
        return self.view

async def main(page: ft.Page):
    page.title = 'Speech + Subtitle Player'
    page.window_height = 800
    await page.update_async()

    app = AudioSubPlayer(speech_dir, speech_file, srt_dir, srt_file)
    
    await page.add_async(app)
    page.overlay.extend([app.pick_speech_file_dialog, app.save_file_dialog])
    page.overlay.append(app.audio1)
    await page.update_async()


ft.app(target=main, assets_dir="assets")
#ft.app(target=main)