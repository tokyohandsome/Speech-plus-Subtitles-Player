'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import numpy as np

speech_dir= "Speech_and_Text/"
speech_file = ''
text_dir = "Speech_and_Text/"
text_file = ''
'''
if speech_file != '':
    text_file = os.path.splitext(os.path.basename(speech_file))[0]+".txt"
    print(text_dir+text_file)
if text_dir+text_file:
    print("File exists.")
'''
def ms_to_hhmmssnnn(milliseconds):
    seconds = int(milliseconds / 1000)
    h = seconds // 3600
    m = (seconds - h * 3600) // 60
    s = seconds - h * 3600 - m * 60
    n = round(milliseconds % 1000)
    return f"{h:02}:{m:02}:{s:02},{n:03}"

    # Convert hh:mm:ss,nnn to milliseconds
def hhmmssnnn_to_ms(time_str):
    try:
        hh, mm, ss_nnn = time_str.split(":")
        hh, mm, ss_nnn = int(hh), int(mm), int(ss_nnn.replace(',' , ''))
        total_seconds = hh * 3600 + mm * 60 + ss_nnn // 1000
        milliseconds = total_seconds * 1000 + ss_nnn % 1000
        return milliseconds
    except ValueError:
        print("Invalid time format. Please use hh:mm:ss,nnn format.")

# Create a list of subtitles from text file.
# subs[n] = [index_number: str, start_time: str, end_time: int, text: str]
def create_subtitles(file):
    subs = []
    sub = []
    counter = 0
    extension = os.path.splitext(file)[1]

    # Source file is ssp file format, one block consists of 4 lines: index, start_time, end_time, text
    if extension == '.ssp':
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
    # Source file is srt file format, one block consists of 4 lines: index, start_time --> end_time, text, empty line
    elif extension == '.srt':
        with open(file, 'r') as h:
            for line in h.readlines():
                # Remove '\n' at the end of each line.
                line = line.rstrip()
                if counter % 4 == 0:
                    # Index
                    sub = sub + [line]
                    counter += 1
                elif counter % 4 == 1:
                    # Start time and End time
                    start_time, end_time = line.split(' --> ')
                    sub = sub + [str(hhmmssnnn_to_ms(start_time)).zfill(8)]
                    sub = sub + [hhmmssnnn_to_ms(end_time)]
                    counter += 1
                elif counter %4 == 2:
                    # Text
                    sub = sub + [line]
                    counter += 1
                else:
                    subs.append(sub)
                    sub = []
                    counter += 1
    return(subs)

class SubButton(ft.UserControl):
    def __init__(self, index, start_time, end_time, text, sub_time_clicked, play_button, save_button):
        super().__init__()
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.sub_time_clicked = sub_time_clicked
        self.play_button = play_button
        self.save_button = save_button
    
    def build(self):
        self.display_start_time = ft.TextButton(text=f"{ms_to_hhmmssnnn(int(self.start_time))}",
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
        self.save_button.text = '*Save'
        await self.play_button.focus_async()
        await self.save_button.update_async()
        await self.update_async()

    async def cancel_clicked(self, e):
        self.display_view.visible = True
        self.edit_view.visible = False
        await self.play_button.focus_async()
        await self.update_async()

    async def jump_clicked(self, e):
        await self.sub_time_clicked(self.start_time)

class AudioSubPlayer(ft.UserControl):
    def __init__(self, speech_dir, speech_file, text_dir, text_file, load_audio):
        super().__init__()
        self.position = 0
        self.duration = 0
        self.isPlaying = False
        self.speech_dir = speech_dir
        self.speech_file = speech_file
        self.text_dir = text_dir
        self.text_file = text_file
        self.load_audio = load_audio

        self.base_dir = ft.Text(value=f"Base Directory: {os.path.dirname(self.speech_file)}")

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

        self.position_text = ft.Text(value='Current position')
        self.duration_text = ft.Text(value='Duration (hh:mm:ss,nnn)')
        
        self.subs_view = ft.Column(
            spacing = 5,
            height= 400,
            #expand=True,
            width = float("inf"),
            scroll = ft.ScrollMode.ALWAYS,
            auto_scroll=False,
        )
        
        self.rewind_button = ft.ElevatedButton(
            icon=ft.icons.REPLAY_5,
            text="5 secs",
            tooltip='Rewind 5 secs',
            on_click=self.rewind_clicked,
        )

        self.faster_sw = ft.Switch(
            label='1.5x',
            value=False,
            on_change=self.playback_rate,
        )

        self.sub_scroller_sw = ft.Switch(
            label='Auto scroll',
            value=True,
        )
        
        self.audio1 = ft.Audio(
            src=self.speech_dir+self.speech_file,
            volume=1,
            balance=0,
            playback_rate=1,
            on_loaded=self.loaded,
            on_position_changed = self.position_changed,
            on_state_changed = self.playback_completed,
        )

        self.save_file_dialog = ft.FilePicker(on_result=self.save_file_result)
        self.save_file_path = ft.Text()

        self.speech_file_button = ft.ElevatedButton(
            text='Open Speech File', 
            icon=ft.icons.RECORD_VOICE_OVER_OUTLINED, 
            on_click=self.pre_pick_speech_file,
        )

        self.pick_speech_file_dialog = ft.FilePicker(on_result=self.pick_speech_file_result)

        self.speech_file_name = ft.Text(value='← Click to open a speech file.')

        self.text_file_button = ft.ElevatedButton(
            text='Open SRT/SSP File',
            icon=ft.icons.TEXT_SNIPPET_OUTLINED,
            on_click=self.pick_text_file,
        )
        
        self.pick_text_file_dialog = ft.FilePicker(on_result=self.pick_text_file_result)

        self.text_file_name = ft.Text(value='↑ Open a speech file first.')

        self.export_dialog = ft.AlertDialog(
            modal = True,
            title = ft.Text('Export text as...'),
            content = ft.Text('Plesae select a file type.'),
            actions = [
                ft.TextButton('SRT', on_click=self.export_srt, tooltip='Standard subtitle format'),
                ft.TextButton('SSP', on_click=self.export_ssp, tooltip='App original format'),
                ft.TextButton('TXT', on_click=self.export_txt, tooltip='Subtitles text only'),
                ft.TextButton('CSV', on_click=self.export_csv, tooltip='Comma separated value'),
                ft.TextButton('Cancel', on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        self.save_button = ft.ElevatedButton(
            text='Save', 
            icon=ft.icons.SAVE_OUTLINED, 
            tooltip='Update current Text/SRT file',
            )
        
        self.export_button = ft.ElevatedButton(
            text='Export as...', 
            icon=ft.icons.SAVE_ALT, 
            on_click=self.open_export_dialog,
            )

        self.save_or_cancel_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Change not saved.'),
            content=ft.Text('Do you want to discard the change?'),
            actions=[
                ft.TextButton('Save', on_click=self.save_file_result),
                ft.TextButton('Open without save', on_click=self.open_without_save, tooltip='Change will be lost.'),
                ft.TextButton('Cancel', on_click=self.close_save_or_cancel_dialog),
            ]
        )
    async def loaded(self, e):
        self.audio_slider.max = int(await self.audio1.get_duration_async())
        self.duration_text.value = f'{ms_to_hhmmssnnn(self.audio_slider.max)}'
        self.audio_slider.divisions = self.audio_slider.max//60
        self.subtitles = create_subtitles(self.text_file)
        self.save_button.text = 'Save'

        # Extract subtitles as buttons
        self.subs_view.controls.clear()
        for i in range(len(self.subtitles)):
            index = self.subtitles[i][0]
            start_time = self.subtitles[i][1]
            end_time = self.subtitles[i][2]
            text = self.subtitles[i][3]
            # Create instance
            sub = SubButton(index, start_time, end_time, text, self.sub_time_clicked, self.play_button, self.save_button)
            self.subs_view.controls.append(sub)
        await self.update_async()

    async def position_changed(self, e):
        self.audio_slider.value = e.data
        print("Position:", self.audio_slider.value)
        self.position_text.value = ms_to_hhmmssnnn(int(e.data))
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
    
    async def playback_rate(self, e):
        if self.faster_sw.value == True:
            self.audio1.playback_rate = 1.5
        else:
            self.audio1.playback_rate = 1
        print(f'Playback rate: {self.audio1.playback_rate}')
        await self.audio1.update_async()

    async def sub_time_clicked(self, start_time):
        await self.audio1.seek_async(int(start_time))
        await self.update_async()
    
    async def scroll_to(self, e):
        end_time = [item[2] for item in self.subtitles]
        index = np.argmin(np.abs(np.array(end_time) - e))
        key=str(self.subtitles[index][0])
        await self.subs_view.scroll_to_async(key=key, duration =1000)
        await self.update_async()
    
    async def pre_pick_speech_file(self, e):
        if self.save_button.text == '*Save':
            print('Save is not done.')
            await self.save_or_cancel()
        else:
            await self.pick_speech_file()
    
    async def pick_speech_file(self):
        await self.pick_speech_file_dialog.pick_files_async(
            dialog_title='Select a speech (audio) file',
            allow_multiple=False,
            allowed_extensions=['mp3', 'm4a', 'wav', 'mp4', 'aiff', 'aac'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    async def pick_speech_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            print(f'e.files = {e.files}')
            #print(f'type(e.files) = {type(e.files)}')
            self.speech_file_name.value = ''.join(map(lambda f: f.name, e.files))
            print(f'File name= {self.speech_file}, type = {type(self.speech_file)}')
            self.speech_file = ''.join(map(lambda f: f.path, e.files))
            print(f'Full path= {self.speech_file}')
            self.audio1.src = self.speech_file
            self.base_dir.value=f"Directory: {os.path.dirname(self.speech_file)}"
            await self.check_text_file()
            #await self.speech_file_name.update_async()
            #await self.audio1.update_async()
            await self.update_async()
            await self.load_audio()
    
    async def pick_text_file(self, e):
        await self.pick_text_file_dialog.pick_files_async(
            dialog_title='Select a text file',
            allow_multiple=False,
            allowed_extensions=['txt', 'srt', 'ssp'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
    
    async def pick_text_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            print(f'e.files = {e.files}')
            self.text_file_name.value = ''.join(map(lambda f: f.name, e.files))
            print(f'File name= {self.text_file}, type = {type(self.text_file)}')
            self.text_file = ''.join(map(lambda f: f.path, e.files))
            print(f'Full path= {self.text_file}')
            #await self.check_text_file()
            await self.update_async()
            await self.load_audio()

    async def check_text_file(self):
        print(self.speech_file)
        self.text_file = os.path.splitext(self.speech_file)[0]+".srt"
        tmp_file = os.path.splitext(self.speech_file)[0]
        if os.path.exists(tmp_file+'.srt'):
            self.text_file = tmp_file+'.srt'
            self.text_file_name.value = os.path.basename(self.text_file)
        elif os.path.exists(tmp_file+'.ssp'):
            self.text_file = tmp_file+'.ssp'
            self.text_file_name.value = os.path.basename(self.text_file)
        else:
            self.text_file, self.text_file_name = 'No Text File.'
        print(self.text_file)

    async def save_or_cancel(self):
        self.page.dialog = self.save_or_cancel_dialog
        self.save_or_cancel_dialog.open = True
        await self.page.update_async()
    
    async def close_save_or_cancel_dialog(self, e):
        self.save_or_cancel_dialog.open = False
        await self.page.update_async()
    
    async def open_without_save(self, e):
        self.save_or_cancel_dialog.open = False
        await self.page.update_async()
        await self.pick_speech_file()

    # Save file dialog
    async def save_file_result(self, e: ft.FilePickerResultEvent):
        self.save_file_path.value = e.path if e.path else "Cancelled!"
        await self.save_file_path.update()
    
    async def export_srt(self, e):
        pass

    async def export_ssp(self, e):
        pass

    async def export_txt(self, e):
        pass

    async def export_csv(self, e):
        pass

    async def open_export_dialog(self, e):
        self.page.dialog = self.export_dialog
        self.export_dialog.open = True
        await self.page.update_async()
    
    async def close_dialog(self, e):
        self.export_dialog.open = False
        await self.page.update_async()

    # *** BUILD METHOD ***
    def build(self):
        self.view = ft.Column(expand=True, controls=[
            ft.Container(content=
                ft.Column(controls=[
                    ft.Row(controls=[
                        self.base_dir,
                    ]),
                    ft.Row(controls=[
                        self.speech_file_button,
                        self.speech_file_name,
                    ]),
                    ft.Row(controls=[
                        self.text_file_button,
                        self.text_file_name,
                        #ft.ElevatedButton(text='Save', icon=ft.icons.SAVE_OUTLINED, tooltip='Update current Text/SRT file'),
                        self.save_button,
                        #ft.ElevatedButton(text='Export as...', icon=ft.icons.SAVE_ALT, on_click=self.open_export_dialog),
                        self.export_button,
                    ]),
                    self.audio_slider,
                    ft.Row([
                        ft.Text(value="00:00:00,000"),
                        self.position_text,
                        self.duration_text,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row(controls=[
                        self.rewind_button,
                        self.play_button,
                        self.faster_sw,
                        self.sub_scroller_sw,
                        #ft.ElevatedButton("Get current position",
                        #    on_click=lambda _: print("Current position:", self.audio1.get_current_position()),)
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

    async def load_audio():
        page.overlay.append(app.audio1)
        print(f'app.audio1 = {app.audio1}')
        print('Load audio file and update page.')
        await page.update_async()

    app = AudioSubPlayer(speech_dir, speech_file, text_dir, text_file, load_audio)
    
    await page.add_async(app)
    page.overlay.extend([app.pick_speech_file_dialog, app.pick_text_file_dialog, app.save_file_dialog])
    #page.overlay.append(app.audio1)
    await page.update_async()


ft.app(target=main, assets_dir="assets")
#ft.app(target=main)