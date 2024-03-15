'''
Supported mp3 sampling rate = 44.1KHz
'''

import flet as ft
import os
import numpy as np
from datetime import datetime

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

    # Source file is txt file which does not have timestamps.
    if extension == '.txt':
        with open(file, 'r') as h:
            index = 1
            for line in h.readlines():
                #print(counter)
                # Remove '\n' at the end of each line.
                line = line.rstrip()
                sub = sub + [index]
                sub = sub + [201355555]
                sub = sub + [0]
                sub = sub + [line]
                subs.append(sub)
                sub = []
                index += 1
    # Source file is srt file format, one block consists of 4 lines: index, start_time --> end_time, text, empty line
    elif extension == '.srt':
        with open(file, 'r') as h:
            index = 1
            for line in h.readlines():
                #print(counter)
                # Remove '\n' at the end of each line.
                line = line.rstrip()
                if counter % 4 == 0:
                    # Index
                    sub = sub + [index]
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
                    if sub[3] =='':
                        sub = []
                        counter += 1
                        continue
                    subs.append(sub)
                    sub = []
                    counter += 1
                    index += 1
    return(subs)

class SubButton(ft.UserControl):
    def __init__(self, index, start_time, end_time, text, sub_time_clicked, play_button, save_button, subtitles):
        super().__init__()
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.sub_time_clicked = sub_time_clicked
        self.play_button = play_button
        self.save_button = save_button
        self.subtitles = subtitles
    
    def build(self):
        self.display_start_time = ft.TextButton(text=f"{ms_to_hhmmssnnn(int(self.start_time))}",
                                           tooltip="Click to jump here",
                                           disabled=(self.start_time==201355555),
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
                ft.Text(value=self.index),
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
        self.edit_text.focus()
        self.display_view.visible = False
        self.edit_view.visible = True
        self.edit_text.on_submit = self.save_clicked
        self.update()

    async def save_clicked(self, e):
        self.display_text.text= self.edit_text.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.save_button.text = '*Save'
        self.subtitles[int(self.index)-1][3]=self.display_text.text
        self.play_button.focus()
        self.save_button.update()
        self.update()

    async def cancel_clicked(self, e):
        self.display_view.visible = True
        self.edit_view.visible = False
        self.play_button.focus()
        self.update()

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
            on_click=self.play_button_clicked,
            disabled=True,
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
            disabled=True,
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
            autofocus=True,
            on_click=self.pre_pick_speech_file,
        )

        self.pick_speech_file_dialog = ft.FilePicker(on_result=self.pick_speech_file_result)

        self.speech_file_name = ft.Text(value='← Click to open a speech file.')

        self.text_file_button = ft.ElevatedButton(
            text='Open SRT/TXT File',
            icon=ft.icons.TEXT_SNIPPET_OUTLINED,
            on_click=self.pick_text_file,
            disabled=True,
        )
        
        self.pick_text_file_dialog = ft.FilePicker(on_result=self.pick_text_file_result)

        self.text_file_name = ft.Text(value='No file selected.')

        self.export_dialog = ft.AlertDialog(
            modal = True,
            title = ft.Text('Export text as...'),
            content = ft.Text('Plesae select a file type.'),
            actions = [
                ft.TextButton('SRT', on_click=self.export_as_srt, tooltip='Subtitles with timestamps',
                              disabled=(os.path.splitext(self.text_file)[1]=='.txt')),
                ft.TextButton('TXT', on_click=self.export_as_txt, tooltip='Subtitles only (no timestamps)'),
                #ft.TextButton('CSV', on_click=self.export_csv, tooltip='Comma separated value'),
                ft.TextButton('Cancel', on_click=self.close_export_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        self.export_as_srt_dialog = ft.FilePicker(on_result=self.export_as_srt_result)
        
        self.export_as_txt_dialog = ft.FilePicker(on_result=self.export_as_txt_result)

        self.save_button = ft.ElevatedButton(
            text='Save', 
            icon=ft.icons.SAVE_OUTLINED, 
            tooltip='Update current Text/SRT file',
            disabled=True,
            on_click=self.save_clicked
            )
        
        self.export_button = ft.ElevatedButton(
            text='Export as...', 
            icon=ft.icons.SAVE_ALT, 
            on_click=self.open_export_dialog,
            disabled=True,
            )

        self.save_or_cancel_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Change not saved.'),
            content=ft.Text('Do you want to discard the change?'),
            actions=[
                #ft.TextButton('Save', on_click=self.save_then_open, tooltip='Save then open another file.'),
                ft.TextButton('Open without save', on_click=self.open_without_save, tooltip='Change will be lost.'),
                ft.TextButton('Cancel', on_click=self.close_save_or_cancel_dialog),
            ]
        )

        self.notification_bar=ft.SnackBar(
            content=ft.Text('Speech + Subtitle Player'),
            duration=2000,
            bgcolor=ft.colors.BLUE_GREY_700,
        )

    async def loaded(self, e):
        self.audio_slider.max = int(await self.audio1.get_duration_async())
        self.duration_text.value = f'{ms_to_hhmmssnnn(self.audio_slider.max)}'
        self.audio_slider.divisions = self.audio_slider.max//60
        self.subtitles = create_subtitles(self.text_file)
        self.save_button.text = 'Save'
        self.save_button.disabled=False
        self.export_button.disabled=False
        self.play_button.disabled=False
        self.play_button.update()
        self.rewind_button.disabled=False
        self.text_file_button.disabled=False
        self.speech_file_button.autofocus=False
        self.speech_file_button.update()
        self.play_button.focus()
        self.notification_bar.content=ft.Text('Speech file loaded.', color=ft.colors.LIGHT_BLUE_ACCENT_400)
        self.notification_bar.bgcolor=ft.colors.BLUE_GREY_700
        self.notification_bar.open=True

        # Extract subtitles as buttons
        self.subs_view.controls.clear()
        for i in range(len(self.subtitles)):
            index = self.subtitles[i][0]
            start_time = self.subtitles[i][1]
            if self.subtitles[0][1]== 201355555:
                self.sub_scroller_sw.value=False
                self.sub_scroller_sw.disabled=True
            else:
                self.sub_scroller_sw.value=True
                self.sub_scroller_sw.disabled=False
            self.sub_scroller_sw.update()
            end_time = self.subtitles[i][2]
            text = self.subtitles[i][3]
            # Create instance
            sub = SubButton(index, start_time, end_time, text, self.sub_time_clicked, self.play_button, 
                            self.save_button, self.subtitles)
            self.subs_view.controls.append(sub)
        '''
        index = 0
        for i in range(len(self.subtitles)):
            text = self.subtitles[i][3]
            if text =='':
                continue
            index += 1
            start_time = self.subtitles[i][1]
            end_time = self.subtitles[i][2]
            # Create instance
            sub = SubButton(index, start_time, end_time, text, self.sub_time_clicked, self.play_button, 
                            self.save_button, self.subtitles)
            self.subs_view.controls.append(sub)
            '''
        self.update()

    async def position_changed(self, e):
        self.audio_slider.value = e.data
        print("Position:", self.audio_slider.value)
        self.position_text.value = ms_to_hhmmssnnn(int(e.data))
        if self.sub_scroller_sw.value == True:
            await self.scroll_to(self.audio_slider.value)
        self.update()

    async def slider_changed(self, e):
        self.audio1.seek(int(self.audio_slider.value))
        print(int(self.audio_slider.value))
        self.update()

    async def play_button_clicked(self, e):
        self.position = await self.audio1.get_current_position_async()
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
    
    async def playback_completed(self, e):
        if e.data == "completed":
            self.isPlaying = False 
            self.play_button.icon=ft.icons.PLAY_ARROW
            self.play_button.text = "Play"
        self.update()
    
    async def rewind_clicked(self, e):
        if self.audio_slider.value <= 5*1000:
            self.audio_slider.value = 0
        else:
            self.audio_slider.value -= 5*1000
        self.audio1.seek(int(self.audio_slider.value))
        print(int(self.audio_slider.value))
        self.update()
    
    async def playback_rate(self, e):
        if self.faster_sw.value == True:
            self.audio1.playback_rate = 1.5
        else:
            self.audio1.playback_rate = 1
        print(f'Playback rate: {self.audio1.playback_rate}')
        await self.audio1.update_async()

    async def sub_time_clicked(self, start_time):
        self.audio1.seek(int(start_time))
        self.update()
    
    async def scroll_to(self, e):
        end_time = [item[2] for item in self.subtitles]
        index = np.argmin(np.abs(np.array(end_time) - e))
        key=str(self.subtitles[index][0])
        self.subs_view.scroll_to(key=key, duration =1000)
        self.update()
    
    async def pre_pick_speech_file(self, e):
        if self.save_button.text == '*Save':
            print('Save is not done.')
            self.save_or_cancel()
        else:
            await self.pick_speech_file()
    
    async def pick_speech_file(self):
        self.pick_speech_file_dialog.pick_files(
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
            #await self.speech_file_name.update()
            #await self.audio1.update()
            self.update()
            await self.load_audio()
    
    async def pick_text_file(self, e):
        self.pick_text_file_dialog.pick_files(
            dialog_title='Select a subtitle file',
            allow_multiple=False,
            allowed_extensions=['txt', 'srt'],
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
            self.update()
            await self.load_audio()

    async def check_text_file(self):
        print(self.speech_file)
        self.text_file = os.path.splitext(self.speech_file)[0]+".srt"
        tmp_file = os.path.splitext(self.speech_file)[0]
        if os.path.exists(tmp_file+'.srt'):
            self.text_file = tmp_file+'.srt'
            self.text_file_name.value = os.path.basename(self.text_file)
        elif os.path.exists(tmp_file+'.txt'):
            self.text_file = tmp_file+'.txt'
            self.text_file_name.value = os.path.basename(self.text_file)
        else:
            self.text_file, self.text_file_name = 'No Text File.'
        print(self.text_file)

    async def save_or_cancel(self):
        self.page.dialog = self.save_or_cancel_dialog
        self.save_or_cancel_dialog.open = True
        self.page.update()
    
    async def close_save_or_cancel_dialog(self, e):
        self.save_or_cancel_dialog.open = False
        self.page.update()
    
    async def open_without_save(self, e):
        self.save_or_cancel_dialog.open = False
        self.page.update()
        self.pick_speech_file()

    # Save file dialog
    async def save_clicked(self, e):
        #print(self.subtitles)
        #print()
        print(f'File: {self.text_file}')
        extension = os.path.splitext(self.text_file)[1]
        print(f'Extension: {extension}')
        #filename = os.path.splitext(self.text_file)[0]+datetime.now().strftime("%Y%m%d%H%M")
        #ext = os.path.splitext(self.text_file)[1] 
        #print(f'filename + ext = {filename+ext}')
        #with open(filename+ext, 'w') as txt:
        '''
        with open(self.text_file, 'w') as txt:
            for i in self.subtitles:
                for j in range(len(i)):
                    if j % 4 == 0:
                        txt.write('%s\n' % i[j])
                    elif j % 4 == 1:
                        start = ms_to_hhmmssnnn(int(i[j]))
                        end = ms_to_hhmmssnnn(i[j+1])
                        txt.write(f'{start} --> {end}\n')
                    elif j % 4 == 3:
                        txt.write('%s\n\n' % i[j])
        '''
        if extension == '.srt':
            await self.save_as_srt(self.text_file)
        elif extension == '.txt':
            await self.save_as_txt(self.text_file)
        self.save_button.text=('Save')
        self.update()

    async def save_file_result(self, e: ft.FilePickerResultEvent):
        self.save_file_path.value = e.path if e.path else "Cancelled!"
        self.save_file_path.update()
    '''
    async def save_then_open(self):
        await self.close_save_or_cancel_dialog()
        await self.save_clicked()
        await self.update()
        await self.pick_speech_file()
    '''
    async def export_as_srt(self, e):
        if os.path.splitext(self.text_file)[1] == '.srt':
            #suggested_file_name = os.path.splitext(self.text_file)[0]+datetime.now().strftime("%Y%m%d%H%M")+'.srt'
            suggested_file_name = os.path.basename(self.text_file).split('.', 1)[0]+'_'+datetime.now().strftime("%Y%m%d%H%M")+'.srt'
        self.export_as_srt_dialog.save_file(
            dialog_title='Export as an SRT file',
            allowed_extensions=['srt'],
            initial_directory=os.path.dirname(text_file),
            file_name = suggested_file_name,
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    async def export_as_srt_result(self, e: ft.FilePicker.result):
        self.export_dialog.open = False
        self.export_dialog.update()
        #self.page.update()
        #self.update()
        if e.path:
            #print(f'e.path= {e.path}')
            #print(f'Filename = {os.path.basename(e.path)}')
            await self.save_as_srt(e.path)
            
    async def export_as_txt(self, e):
        if os.path.exists(os.path.splitext(self.text_file)[0]+'.txt'):
            suggested_file_name = os.path.basename(self.text_file).split('.', 1)[0]+'_'+datetime.now().strftime("%Y%m%d%H%M")+'.txt'
        else:
            suggested_file_name = os.path.basename(self.text_file).split('.', 1)[0]+'.txt'
        self.export_as_txt_dialog.save_file(
            dialog_title='Export as a TXT file',
            allowed_extensions=['txt'],
            initial_directory=os.path.dirname(text_file),
            file_name = suggested_file_name,
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    async def export_as_txt_result(self, e: ft.FilePicker.result):
        self.export_dialog.open = False
        self.export_dialog.update()
        #self.page.update()
        #self.update()
        if e.path:
            #print(f'e.path= {e.path}')
            #print(f'Filename = {os.path.basename(e.path)}')
            await self.save_as_txt(e.path)
            
    # Save as .srt file
    async def save_as_srt(self, save_file_name):
        with open(save_file_name, 'w') as srt:
            for i in self.subtitles:
                for j in range(len(i)):
                    if j % 4 == 0:
                        srt.write('%s\n' % i[j])
                    elif j % 4 == 1:
                        start = ms_to_hhmmssnnn(int(i[j]))
                        end = ms_to_hhmmssnnn(i[j+1])
                        srt.write(f'{start} --> {end}\n')
                    elif j % 4 == 3:
                        srt.write('%s\n\n' % i[j]) 
        self.notification_bar.content=ft.Text(f'Saved {os.path.basename(save_file_name)}.', color=ft.colors.LIGHT_BLUE_ACCENT_400)
        self.notification_bar.bgcolor=ft.colors.BLUE_GREY_700
        self.notification_bar.open=True
        self.update()

    # Save as .txt file
    async def save_as_txt(self, save_file_name):
        with open(save_file_name, 'w') as txt:
            for i in self.subtitles:
                for j in range(len(i)):
                    if j % 4 == 3:
                        txt.write('%s\n' % i[j]) 
        self.notification_bar.content=ft.Text(f'Saved {os.path.basename(save_file_name)}.', color=ft.colors.LIGHT_BLUE_ACCENT_400)
        self.notification_bar.bgcolor=ft.colors.BLUE_GREY_700
        self.notification_bar.open=True
        self.update()

    async def export_csv(self, e):
        pass

    async def open_export_dialog(self, e):
        self.page.dialog = self.export_dialog
        self.export_dialog.open = True
        self.page.update()

    async def close_export_dialog(self, e):
        self.export_dialog.open = False
        self.page.update()
    
    async def close_overwrite_dialog(self, e):
        self.overwrite_dialog.open = False
        self.page.update()

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
                        self.save_button,
                        self.export_button,
                    ]),
                    self.audio_slider,
                    ft.Row([
                        #ft.Text(value="00:00:00,000"),
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
            ),
            ft.Container(content=
                self.notification_bar)
            ],
            )
        
        #return ft.Column(expand=True, controls=self.view)
        return self.view

async def main(page: ft.Page):
    page.title = 'Speech + Subtitle Player'
    page.window_height = 800
    page.update()

    async def load_audio():
        page.overlay.append(app.audio1)
        print(f'app.audio1 = {app.audio1}')
        print('Load audio file and update page.')
        page.update()

    app = AudioSubPlayer(speech_dir, speech_file, text_dir, text_file, load_audio)
    
    page.add(app)
    page.overlay.extend([app.pick_speech_file_dialog, app.pick_text_file_dialog, app.save_file_dialog, 
                         app.export_as_srt_dialog, app.export_as_txt_dialog])
    #page.overlay.append(app.audio1)
    page.update()


ft.app(target=main, assets_dir="assets")
#ft.app(target=main)