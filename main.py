import flet as ft
import os
#import numpy as np
from datetime import datetime

# Convert milliseconds to hh:mm:ss,nnn
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

# Function to create a list of subtitles from text file.
# subs[n] = [[index_number: int, start_time: str, end_time: int, text: str],...]
def create_subtitles(file):
    subs = []
    sub = []
    counter = 0
    extension = os.path.splitext(file)[1]

    # TXT file which does not have timestamps.
    if extension == '.txt':
        with open(file, 'r') as h:
            index = 1
            for line in h.readlines():
                # Remove '\n' at the end of each line.
                line = line.rstrip()
                sub = sub + [index]
                sub = sub + [201355555] # 20135555ms = 55:55:55,555, dummy timestamp for TXT file.
                sub = sub + [0]
                sub = sub + [line]
                subs.append(sub)
                sub = []
                index += 1
    # SRT format, one block consists of 4 lines: index, start_time --> end_time, text, and empty line.
    elif extension == '.srt':
        with open(file, 'r') as h:
            index = 1
            for line in h.readlines():
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
                    # Skip if text is blank. Avoid Whisper's known issue.
                    if sub[3] =='':
                        sub = []
                        counter += 1
                        continue
                    subs.append(sub)
                    sub = []
                    counter += 1
                    index += 1
    return(subs)

# Create button of subtitle text.
class SubButton(ft.UserControl):
    def __init__(self, index, start_time, end_time, text, sub_time_clicked, play_button, save_button, subtitles):
        super().__init__()
        # Parameter of each subtitle.
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        # Passed methods and controls to call and update.
        self.sub_time_clicked = sub_time_clicked
        self.play_button = play_button
        self.save_button = save_button
        self.subtitles = subtitles
    
    # === BUILD METHOD ===
    def build(self):
        # Start time button
        self.display_start_time = ft.TextButton(text=f"{ms_to_hhmmssnnn(int(self.start_time))}",
                                            # Disable jump button if loaded text is TXT, no timestamp.
                                            disabled=(self.start_time==201355555),
                                            # When enabled, jump to the key when clicked.
                                            key=self.index,
                                            width=130,
                                            on_click=self.jump_clicked,)

        # Subtitle text button in display view. Click to edit.
        self.display_text= ft.TextButton(text=f"{self.text}", 
                                         on_click=self.edit_clicked, 
                                         tooltip='Click to edit')

        # Placeholder of subtitle text button in edit view.
        self.edit_text = ft.TextField(expand=1)

        # Put controls together. Left item is the key=index.
        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Text(value=self.index, width=30),
                self.display_start_time,
                self.display_text,
            ]
        )

        # Change tool tip of start time button which is only clickable for SRT.
        if self.start_time==201355555:
            self.display_start_time.tooltip='Jump not available'
        else:
            self.display_start_time.tooltip='Click to jump here'
        
        # Subtitle edit view visible when clicked.
        self.edit_view = ft.Row(
            visible=False,
            #alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            #vertical_alignment=ft.CrossAxisAlignment.CENTER,
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

    # === Methods ===

    # Opens editable text button with subtitle. Hit enter key or click checkmark to call save_clicked.
    async def edit_clicked(self, e):
        self.edit_text.value = self.display_text.text
        self.edit_text.focus()
        self.display_view.visible = False
        self.edit_view.visible = True
        self.edit_text.on_submit = self.save_clicked
        self.update()

    # Updates edited subtitle, change save button, revert focus back to Play button.
    async def save_clicked(self, e):
        self.display_text.text= self.edit_text.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.save_button.text = '*Save'
        self.subtitles[int(self.index)-1][3]=self.display_text.text
        self.play_button.focus()
        self.save_button.update()
        self.update()

    # Closes if edit canceled.
    async def cancel_clicked(self, e):
        self.display_view.visible = True
        self.edit_view.visible = False
        self.play_button.focus()
        self.update()

    # When timestamp clicked calls AudioSubPlayer.sub_time_clicked to jump to button position.
    async def jump_clicked(self, e):
        await self.sub_time_clicked(self.start_time)

# Main class of the app
class AudioSubPlayer(ft.UserControl):
    def __init__(self, load_audio):
        super().__init__()
        self.position = 0
        self.duration = 0
        self.isPlaying = False
        self.load_audio = load_audio

        # == Controls ==
        
        # Audio control with default properties
        self.audio1 = ft.Audio(
            src='',
            volume=1,
            balance=0,
            playback_rate=1,
            on_loaded=self.loaded,
            on_position_changed = self.position_changed,
            on_state_changed = self.playback_completed,
        )

        # Path of the audio file
        self.base_dir = ft.Text(value=f"Base Directory: ")

        # Open speech file button
        self.speech_file_button = ft.ElevatedButton(
            text='Open Speech File', 
            icon=ft.icons.RECORD_VOICE_OVER_OUTLINED, 
            width=210,
            on_click=self.pre_pick_speech_file,
        )

        # Speech file picker control
        self.pick_speech_file_dialog = ft.FilePicker(on_result=self.pick_speech_file_result)

        # Speech file name
        self.speech_file_name = ft.Text(value='← Click to open a speech file.')

        # Alert dialog that opens if subtitle was edited but not saved when Open Speech File button is clicked.
        self.speech_save_or_cancel_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Change not saved.'),
            content=ft.Text('Do you want to discard the change?'),
            actions=[
                #ft.TextButton('Save', on_click=self.save_then_open, tooltip='Save then open another file.'),
                ft.TextButton('Open without save', on_click=self.open_speech_without_save, tooltip='Change will be lost.'),
                ft.TextButton('Cancel', on_click=self.close_speech_save_or_cancel_dialog),
            ]
        )

        # Open text file button
        self.text_file_button = ft.ElevatedButton(
            text='Open SRT/TXT File',
            icon=ft.icons.TEXT_SNIPPET_OUTLINED,
            on_click=self.pre_pick_text_file,
            disabled=True,
            width=210,
        )
        
        # Text file picker control
        self.pick_text_file_dialog = ft.FilePicker(on_result=self.pick_text_file_result)

        # Text file name
        self.text_file_name = ft.Text(value='No file selected.')

        # Save button to update edited subtitles. No dialog, it just overwrites current text file.
        self.save_button = ft.ElevatedButton(
            text='Save', 
            icon=ft.icons.SAVE_OUTLINED, 
            tooltip='Update current SRT/TXT file.',
            disabled=True,
            on_click=self.save_clicked
            )
        
        # Export as SRT button which opens a save dialog. Only available when SRT is open because SRT needs timestamp.
        self.export_as_srt_button = ft.ElevatedButton(
            text = 'SRT',
            icon=ft.icons.SAVE_ALT,
            on_click=self.export_as_srt,
            disabled=True,
            tooltip='Export as SRT file.'
        )

        # Export as SRT file picker
        self.export_as_srt_dialog = ft.FilePicker(on_result=self.export_as_srt_result)

        # Export as TXT button which opens a save dialog. TXT has not timestamp, subtitle text only.
        self.export_as_txt_button = ft.ElevatedButton(
            text = 'TXT',
            icon=ft.icons.SAVE_ALT,
            on_click=self.export_as_txt,
            disabled=True,
            tooltip='Export as TXT file.'
        )

        # Export as TXT file picker
        self.export_as_txt_dialog = ft.FilePicker(on_result=self.export_as_txt_result)

        # Export button to open a dialog (not in use)
        self.export_button = ft.ElevatedButton(
            text='Export as...', 
            icon=ft.icons.SAVE_ALT, 
            on_click=self.open_export_dialog,
            disabled=True,
            )
        
        # Export as dialog (not in use)
        self.export_dialog = ft.AlertDialog(
            modal = True,
            title = ft.Text('Export text as...'),
            content = ft.Text('Plesae select a file type.'),
            actions = [
                ft.TextButton('SRT', on_click=self.export_as_srt, tooltip='Subtitles with timestamps'),
                ft.TextButton('TXT', on_click=self.export_as_txt, tooltip='Subtitles only (no timestamps)'),
                #ft.TextButton('CSV', on_click=self.export_csv, tooltip='Comma separated value'),
                # I guess no one needs subtitles in CSV...
                ft.TextButton('Cancel', on_click=self.close_export_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # Alert dialog that opens if subtitle was edited but not saved when Open SRT/TXT File button is clicked.
        self.text_save_or_cancel_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Change not saved.'),
            content=ft.Text('Do you want to discard the change?'),
            actions=[
                #ft.TextButton('Save', on_click=self.save_then_open, tooltip='Save then open another file.'),
                ft.TextButton('Open without save', on_click=self.open_text_without_save, tooltip='Change will be lost.'),
                ft.TextButton('Cancel', on_click=self.close_text_save_or_cancel_dialog),
            ]
        )
        # Audio position slider
        self.audio_slider = ft.Slider(
            min = 0,
            value = int(self.position/10000),
            label = "{value}ms",
            on_change = self.slider_changed,
        )

        # Current playing position and duration of audio file
        self.position_text = ft.Text(value='Current position')
        self.duration_text = ft.Text(value='Duration (hh:mm:ss,nnn)')
        
        # Rewinds 5 seconds
        self.rewind_button = ft.ElevatedButton(
            icon=ft.icons.REPLAY_5,
            text="5 secs",
            tooltip='Rewind 5 secs',
            on_click=self.rewind_clicked,
            disabled=True,
        )

        # Play/Pause button. After loading audio file, this button will always be focused (space/enter to play/pause).
        self.play_button = ft.ElevatedButton(
            icon=ft.icons.PLAY_ARROW,
            text = "Play",
            on_click=self.play_button_clicked,
            disabled=True,
        )

        # 1.5x faster toggle switch
        self.faster_sw = ft.Switch(
            label='1.5x',
            value=False,
            on_change=self.playback_rate,
        )

        # Auto scroll toggle switch
        self.sub_scroller_sw = ft.Switch(
            label='Auto scroll',
            value=True,
        )
                
        # Area to add subtitles as buttons
        self.subs_view = ft.Column(
            spacing = 5,
            height= 400,
            width = float("inf"),
            scroll = ft.ScrollMode.ALWAYS,
            auto_scroll=False,
        )

        # Notification bar control at the bottom
        self.notification_bar=ft.SnackBar(
            content=ft.Text('Speech + Subtitle Player'),
            duration=2000,
            bgcolor=ft.colors.BLUE_GREY_700,
        )

    # === METHODS ===
    # Called once audio file is loaded. Enable/disable buttons, create subtitles list, etc.
    async def loaded(self, e):
        self.audio_slider.max = int(await self.audio1.get_duration_async())
        self.duration_text.value = f'{ms_to_hhmmssnnn(self.audio_slider.max)}'
        self.audio_slider.divisions = self.audio_slider.max//1000
        # Enables buttons if associated text file exists.
        if self.text_file != 'No Text File.':
            # Call function to create the list of subtitles, self.subtitles.
            self.subtitles = create_subtitles(self.text_file)
            self.save_button.text = 'Save'
            self.save_button.disabled=False
            self.export_button.disabled=False
            self.export_as_srt_button.disabled=False
            self.export_as_txt_button.disabled=False
        # Disable buttons if associated text file does not eixt.
        else:
            self.save_button.disabled=True
            self.export_button.disabled=True
            self.export_as_srt_button.disabled=True
            self.export_as_txt_button.disabled=True
            self.subtitles = []
        self.speech_file_button.autofocus=False
        self.speech_file_button.update()
        self.play_button.disabled=False
        self.play_button.focus()
        self.play_button.autofocus=True
        self.play_button.update()
        self.rewind_button.disabled=False
        self.text_file_button.disabled=False
        self.subs_view.controls.clear()
        
        # Create buttons of subtitles from the list self.subtitles.
        if self.subtitles != []:
            # .txt or .srt file
            for i in range(len(self.subtitles)):
                index = self.subtitles[i][0]
                start_time = self.subtitles[i][1]
                # .txt file (timestap is dummy, 55:55:55,555) disable buttons.
                if self.subtitles[0][1]== 201355555:
                    self.sub_scroller_sw.value=False
                    self.sub_scroller_sw.disabled=True
                    self.export_dialog.actions[0].disabled=True
                    self.export_as_srt_button.disabled=True
                # .srt file
                else:
                    self.sub_scroller_sw.value=True
                    self.sub_scroller_sw.disabled=False
                self.sub_scroller_sw.update()
                end_time = self.subtitles[i][2]
                text = self.subtitles[i][3]
                
                # Create button instance of each subtitle. Include methods and controls for the instance to call or update.
                sub = SubButton(index, start_time, end_time, text, self.sub_time_clicked, self.play_button, 
                                self.save_button, self.subtitles)

                # Add button to the subtitle button area, subs_view.
                self.subs_view.controls.append(sub)

            # Call snackbar to show a notification.
            notification = f'Subtitle file loaded: {os.path.basename(self.text_file)}'
            await self.open_notification_bar(notification)
        
        # No text file found. Call snackbar to show an alert.
        else:
            notification = f'Subtitle file (.srt or .txt) not found.'
            await self.open_notification_bar(notification, type='error')
            print('Subtitle file not found.')

        self.update()

    # Called every second automatically. Update slider value.
    async def position_changed(self, e):
        self.audio_slider.value = e.data
        #print("Position:", self.audio_slider.value)
        self.position_text.value = ms_to_hhmmssnnn(int(e.data))
        if (self.sub_scroller_sw.value == True) and (self.text_file_name.value != 'No Text File.'):
            await self.scroll_to(self.audio_slider.value)
        self.update()

    # Called if slider position is changed by user. Move audio play position.
    async def slider_changed(self, e):
        self.audio1.seek(int(self.audio_slider.value))
        #print(int(self.audio_slider.value))
        self.update()

    # Change Play/Pause status and icon when called.
    async def play_button_clicked(self, e):
        self.position = await self.audio1.get_current_position_async()
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
    
    # When audio playback is complete, reset play button and status.
    async def playback_completed(self, e):
        if e.data == "completed":
            self.isPlaying = False 
            self.play_button.icon=ft.icons.PLAY_ARROW
            self.play_button.text = "Play"
        self.update()
    
    # When 5 secs button is clicked, rewind 5 seconds.
    async def rewind_clicked(self, e):
        if self.audio_slider.value <= 5*1000:
            self.audio_slider.value = 0
        else:
            self.audio_slider.value -= 5*1000
        self.audio1.seek(int(self.audio_slider.value))
        #print(int(self.audio_slider.value))
        self.update()
    
    # Switch playback rate between normal and 1.5x faster.
    async def playback_rate(self, e):
        if self.faster_sw.value == True:
            self.audio1.playback_rate = 1.5
        else:
            self.audio1.playback_rate = 1
        #print(f'Playback rate: {self.audio1.playback_rate}')
        await self.audio1.update_async()

    # When the timestamp is clicked, jump to its position and play if not playing.
    async def sub_time_clicked(self, start_time):
        self.audio1.seek(int(start_time))
        if self.isPlaying == False:
            await self.play_button_clicked(start_time)
        self.update()
    
    # Called when slider position is changed and scroll to subtitle with the nearest end_time.
    async def scroll_to(self, e):
        end_time = [item[2] for item in self.subtitles]
        # Numpy is only used below:
        #index = np.argmin(np.abs(np.array(end_time) - e))
        # Below works without using Numpy:
        index = min(range(len(end_time)), key=lambda i: abs(end_time[i]-e))
        key=str(self.subtitles[index][0])
        self.subs_view.scroll_to(key=key, duration =1000)
        self.update()
    
    # Called once Open Speech File button is clicked to pause playback and check if changes saved.
    async def pre_pick_speech_file(self, e):
        if self.isPlaying == True:
            await self.play_button_clicked(e)
        if self.save_button.text == '*Save':
            #print('Save is not done.')
            await self.speech_save_or_cancel()
        else:
            await self.pick_speech_file()
    
    # Opens audio file pick dialog. Only allow compatible extensions.
    async def pick_speech_file(self):
        self.pick_speech_file_dialog.pick_files(
            dialog_title='Select a speech (audio) file',
            allow_multiple=False,
            allowed_extensions=['mp3', 'm4a', 'wav', 'mp4', 'aiff', 'aac'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    # Called when audio file pick dialog is closed. If file is selected, call self.check_text_file to load text file.
    async def pick_speech_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            #print(f'e.files = {e.files}')
            self.speech_file_name.value = ''.join(map(lambda f: f.name, e.files))
            self.speech_file = ''.join(map(lambda f: f.path, e.files))
            #print(f'Full path= {self.speech_file}')
            self.audio1.src = self.speech_file
            self.base_dir.value=f"Directory: {os.path.dirname(self.speech_file)}"
            await self.check_text_file()
            self.update()
            await self.load_audio()
    
    # Called once Open Speech File button is clicked to pause playback and check if changes saved.
    async def pre_pick_text_file(self, e):
        if self.isPlaying == True:
            await self.play_button_clicked(e)
        if self.save_button.text == '*Save':
            #print('Save is not done.')
            await self.text_save_or_cancel()
        else:
            await self.pick_text_file()
    
    # Opens text file pick dialog. Only allow txt or srt extensions.
    async def pick_text_file(self):
        self.pick_text_file_dialog.pick_files(
            dialog_title='Select a subtitle file',
            allow_multiple=False,
            allowed_extensions=['txt', 'srt'],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
    
    # Called when text file pick dialog is closed. If file is selected, call self.load_audio() which initializes everything.
    async def pick_text_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            #print(f'e.files = {e.files}')
            self.text_file_name.value = ''.join(map(lambda f: f.name, e.files))
            #print(f'File name= {self.text_file}, type = {type(self.text_file)}')
            self.text_file = ''.join(map(lambda f: f.path, e.files))
            #print(f'Full path= {self.text_file}')
            self.update()
            await self.load_audio()

    # Checks if audioFileName.srt or .txt exists to automatically load it.
    async def check_text_file(self):
        #print(f'Speech file = {self.speech_file}')
        tmp_file = os.path.splitext(self.speech_file)[0]
        if os.path.exists(tmp_file+'.srt'):
            self.text_file = tmp_file+'.srt'
            self.text_file_name.value = os.path.basename(self.text_file)
        elif os.path.exists(tmp_file+'.txt'):
            self.text_file = tmp_file+'.txt'
            self.text_file_name.value = os.path.basename(self.text_file)
        else:
            self.text_file = self.text_file_name.value = 'No Text File.'
            self.save_button.disabled=True
            self.export_button.disabled=True
            self.sub_scroller_sw.disabled=True
        #print(f'Subtitle file = {self.text_file_name.value}')

    # Opens a dialog if change is not saved.
    async def speech_save_or_cancel(self):
        self.page.dialog = self.speech_save_or_cancel_dialog
        self.speech_save_or_cancel_dialog.open = True
        self.page.update()
    
    # Closes the above dialog.
    async def close_speech_save_or_cancel_dialog(self, e):
        self.speech_save_or_cancel_dialog.open = False
        self.page.update()
    
    # Opens audio file pick.
    async def open_speech_without_save(self, e):
        self.speech_save_or_cancel_dialog.open = False
        self.page.update()
        await self.pick_speech_file()

    # Opens a dialog if change is not saved.
    async def text_save_or_cancel(self):
        self.page.dialog = self.text_save_or_cancel_dialog
        self.text_save_or_cancel_dialog.open = True
        self.page.update()
        
    # Closes the above dialog.
    async def close_text_save_or_cancel_dialog(self, e):
        self.text_save_or_cancel_dialog.open = False
        self.page.update()

    # Opens text file pick.
    async def open_text_without_save(self, e):
        self.text_save_or_cancel_dialog.open = False
        self.page.update()
        await self.pick_text_file()
    
    # Updates current open file.
    async def save_clicked(self, e):
        #print(f'File: {self.text_file}')
        extension = os.path.splitext(self.text_file)[1]
        #print(f'Extension: {extension}')
        if self.save_button.text==('*Save'):
            if extension == '.srt':
                await self.save_as_srt(self.text_file)
            elif extension == '.txt':
                await self.save_as_txt(self.text_file)
            self.save_button.text=('Save')
        self.update()

    # Exports current open SRT file as another SRT file.
    async def export_as_srt(self, e):
        if os.path.splitext(self.text_file)[1] == '.srt':
            suggested_file_name = os.path.basename(self.text_file).split('.', 1)[0]+'_'+datetime.now().strftime("%Y%m%d%H%M")+'.srt'
        self.export_as_srt_dialog.save_file(
            dialog_title='Export as an SRT file',
            allowed_extensions=['srt'],
            file_name = suggested_file_name,
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    # Checks result of Export as SRT File Picker and passes absolute path to self.save_as_srt if exists.
    async def export_as_srt_result(self, e: ft.FilePicker.result):
        if e.path:
            await self.save_as_srt(e.path)
            
    # Saves as .srt file.
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
        notification = f'Subtitle saved as an SRT file: {os.path.basename(save_file_name)}'
        await self.open_notification_bar(notification)
        self.update()

    # Exports current open text file as a TXT file.
    async def export_as_txt(self, e):
        if os.path.exists(os.path.splitext(self.text_file)[0]+'.txt'):
            suggested_file_name = os.path.basename(self.text_file).split('.', 1)[0]+'_'+datetime.now().strftime("%Y%m%d%H%M")+'.txt'
        else:
            suggested_file_name = os.path.basename(self.text_file).split('.', 1)[0]+'.txt'
        self.export_as_txt_dialog.save_file(
            dialog_title='Export as a TXT file',
            allowed_extensions=['txt'],
            file_name = suggested_file_name,
            file_type=ft.FilePickerFileType.CUSTOM,
        )

    # Checks result of Export as TXT File Picker and passes absolute path to self.save_as_txt if exists.
    async def export_as_txt_result(self, e: ft.FilePicker.result):
        if e.path:
            await self.save_as_txt(e.path)
            
    # Saves as .txt file.
    async def save_as_txt(self, save_file_name):
        with open(save_file_name, 'w') as txt:
            for i in self.subtitles:
                for j in range(len(i)):
                    if j % 4 == 3:
                        txt.write('%s\n' % i[j]) 
        notification = f'Subtitle saved as a TXT file: {os.path.basename(save_file_name)}'
        await self.open_notification_bar(notification)
        self.update()
    
    # Opens notification bar with given text. If type is 'error', shows message longer with highlight.
    async def open_notification_bar(self, notification, type='normal'):
        if type == 'normal':
            self.notification_bar.content=ft.Text(notification, color=ft.colors.LIGHT_BLUE_ACCENT_400)
            self.notification_bar.bgcolor=ft.colors.BLUE_GREY_700
        elif type == 'error':
            self.notification_bar.content=ft.Text(notification, color=ft.colors.RED)
            self.notification_bar.bgcolor=ft.colors.YELLOW
            self.notification_bar.duration=4000
        self.notification_bar.open=True 
        self.notification_bar.update()

    # Placeholder for export as CSV.
    async def export_csv(self, e):
        pass

    # Opens/closes export dialg (not in use).
    async def open_export_dialog(self, e):
        self.page.dialog = self.export_dialog
        self.export_dialog.open = True
        self.page.update()
    async def close_export_dialog(self, e):
        self.export_dialog.open = False
        self.page.update()
    
    # === BUILD METHOD ===
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
                        #self.export_button,
                        self.export_as_srt_button,
                        self.export_as_txt_button,
                    ]),
                    self.audio_slider,
                    ft.Row([
                        self.position_text,
                        self.duration_text,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row(controls=[
                        self.rewind_button,
                        self.play_button,
                        self.faster_sw,
                        self.sub_scroller_sw,
                    ]),
                ]), expand=False, border_radius=10, border=ft.border.all(1), padding=10, 
            ),
            ft.Container(content=
                self.subs_view,
                border_radius=10,
                border=ft.border.all(1),
                padding=5,
            ),
            ft.Row(controls=[
                ft.Text(text_align=ft.CrossAxisAlignment.START,
                        spans=[ft.TextSpan('© 2024 Peddals.com', url="https://blog.peddals.com")],
                        ), 
                ft.Image(src='in_app_logo_small.png'),
            ],alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(content=
                self.notification_bar)
            ],
            )
        
        return self.view

# Main function that builds window and adds page. Also, adds audio file and dialogs that are invisible as overlay.
async def main(page: ft.Page):
    page.title = 'Speech + Subtitles Player'
    page.window_height = 800
    page.theme_mode=ft.ThemeMode.SYSTEM
    page.update()

    # Appends audio as an overlay to the page.
    async def load_audio():
        page.overlay.append(app.audio1)
        page.update()

    # Creates an instance of AudioSubPlayer class. Passes load_audio for the instance to append audio to the page. 
    app = AudioSubPlayer(load_audio)
    page.add(app)

    # Adds dialog instance methods to the page.
    page.overlay.extend([app.pick_speech_file_dialog, app.pick_text_file_dialog, 
                         app.export_as_srt_dialog, app.export_as_txt_dialog])
    page.update()


ft.app(target=main, assets_dir="assets")