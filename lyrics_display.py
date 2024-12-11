import tkinter as tk
import pygame
import time
import ctypes
import os
import sys
import json
from lrc_srt_convert import convert
from vtt2srt import vtt_to_srt
from config_manager import ConfigManager

class LyricsDisplay(tk.Tk):
    def __init__(self, music_file, main_window, subtitle_file=None):
        super().__init__()
        
        self.main_window = main_window
        
        # 初始化pygame音频(仅在播放音乐时)
        if music_file:
            pygame.mixer.init()
            self.volume = 0.5
            pygame.mixer.music.set_volume(self.volume)
        
        # 读取配置文件
        self.config = self.load_config()
        
        # 获取字幕文件路径
        if subtitle_file:
            lyrics_file = subtitle_file
        elif music_file:
            # 尝试不同的字幕文件命名格式
            base_name = os.path.splitext(music_file)[0]
            music_name = os.path.basename(music_file)
            possible_lyrics = [
                base_name + '.lrc',                    # a.lrc
                base_name + '.srt',                    # a.srt
                base_name + '.vtt',                    # a.vtt
                music_file + '.lrc',                   # a.mp3.lrc
                music_file + '.srt',                   # a.mp3.srt
                music_file + '.vtt',                   # a.mp3.vtt
                os.path.join(os.path.dirname(music_file), 'lyrics', os.path.basename(base_name) + '.lrc'),    # lyrics/a.lrc
                os.path.join(os.path.dirname(music_file), 'lyrics', music_name + '.lrc'),                     # lyrics/a.mp3.lrc
            ]
            
            # 查找存在的字幕文件
            lyrics_file = None
            for possible_file in possible_lyrics:
                if os.path.exists(possible_file):
                    lyrics_file = possible_file
                    break
                    
            if not lyrics_file:
                print("找不到对应的字幕文件!")
                sys.exit()
        else:
            sys.exit()
        
        # 处理不同格式的字幕文件
        if lyrics_file.endswith('.srt'):
            lrc_file = lyrics_file.replace('.srt', '.lrc')
            convert(lyrics_file, lrc_file)
            lyrics_file = lrc_file
        elif lyrics_file.endswith('.vtt'):
            srt_file = lyrics_file.replace('.vtt', '.srt')
            vtt_to_srt(lyrics_file)
            lrc_file = srt_file.replace('.srt', '.lrc')
            convert(srt_file, lrc_file)
            lyrics_file = lrc_file
            
        self.lyrics = self.load_lyrics(lyrics_file)
        self.current_index = 0
        self.is_paused = False
        self.pause_time = 0
        self.music_file = music_file
        self.music_start_time = time.time()
        
        # 如果有音乐文件则播放
        if music_file:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play()
        
        #告诉操作系统使用程序自身的dpi适配
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        #获取屏幕的缩放因子
        ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0)
        #设置程序缩放
        self.tk.call('tk', 'scaling', ScaleFactor/75)

        # 从配置文件中读取字体和颜色
        self.font_family = self.config["font"]["family"]
        self.font_size = self.config["font"]["size"]
        self.font_color = self.config["font"]["color"]
        
        self.time_font_family = self.config["time_font"]["family"]
        self.time_font_size = self.config["time_font"]["size"]
        self.time_font_color = self.config["time_font"]["color"]

        # 从配置文件读取窗口尺寸和位置
        self.window_width = self.config["window"]["width"]
        self.window_height = self.config["window"]["height"]
        self.initial_x = self.config["window"]["initial_position"]["x"]
        self.initial_y = self.config["window"]["initial_position"]["y"]

        # 透明窗体
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.4)

        # 设置无边框窗体
        self.overrideredirect(True)
        self.geometry(f"{self.window_width}x{self.window_height}+{self.initial_x}+{self.initial_y}")
        self.configure(bg="black")

        # 时间标签，用于显示当前时间
        self.time_label = tk.Label(self, font=(self.time_font_family, self.time_font_size), fg=self.time_font_color, bg="black")
        self.time_label.pack(fill=tk.X, side=tk.TOP)

        # 歌词标签，用于显示歌词
        self.label = tk.Label(self, font=(self.font_family, self.font_size), fg=self.font_color, bg="black", anchor="center")
        self.label.pack(fill=tk.BOTH)

        # 初始位置
        self.initial_x = 0
        self.initial_y = 0

        # 绑定鼠标件到container上，使整个背景区域都可以拖动
        self.bind("<ButtonPress-1>", self.on_button_press)
        self.bind("<B1-Motion>", self.on_mouse_drag)

        # 绑定键盘事件
        self.bind("<Left>", self.rewind_1_second)  # 左箭头回退1秒
        self.bind("<Right>", self.fast_forward_1_second)  # 右箭头快进1秒
        self.bind("<Control-c>", self.quit_program)  # 绑定 Ctrl+C 退出程序
        self.bind("<space>", self.toggle_pause)  # 绑定空格键暂停/续
        self.bind("<Prior>", self.fast_forward_1_minute)  # PageUp快进1分钟
        self.bind("<Next>", self.rewind_1_minute)  # PageDown快退1分钟
        self.bind("<Up>", self.volume_up)  # 向上键增加音量
        self.bind("<Down>", self.volume_down)  # 向下键降低音量
        self.bind("<Escape>", self.return_to_main)  # ESC键返回主界面
        self.after(100, self.update_lyric)  # 每 100 毫秒更新一次歌词
    
        
    def return_to_main(self, event=None):
        self.save_window_position()
        pygame.mixer.music.stop()
        self.destroy()
        # 如果是从文件夹打开的,则返回主界面,否则退出程序
        if len(self.main_window.playlist) > 1:
            self.main_window.deiconify()
        else:
            self.main_window.destroy()
    
    def volume_up(self, event):
        """增加音量"""
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)
        
    def volume_down(self, event):
        """降低音量"""
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)
        
    def quit_program(self, event=None):
        """退出程序"""
        self.save_window_position()
        if hasattr(pygame.mixer, 'music') and self.music_file:  # 检查 pygame.mixer 是否已初始化
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except pygame.error:
                pass  # 忽略 pygame 相关错误
        self.main_window.destroy()
        self.quit()
        self.destroy()
    
    def load_config(self):
        """加载配置文件"""
        if getattr(sys, 'frozen', False):
            config_path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')
        else:
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {config_path} not found!")
            return None

    def load_lyrics(self, lyrics_file):
        lyrics = []
        with open(lyrics_file, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():
                    try:
                        time_str, text = line.split(']')  # 获取时间戳和歌词文本
                        time_str = time_str.strip('[')  # 去除 '['
                        # 检查是否是有效的时间戳格式（包含冒号）
                        if ':' in time_str:
                            minutes, seconds = map(float, time_str.split(':'))
                            time_in_seconds = minutes * 60 + seconds  # 转换为秒
                            lyrics.append((time_in_seconds, text.strip()))
                    except (ValueError, IndexError):
                        # 跳过无法解析的行（比如元数据标签）
                        continue
        return sorted(lyrics, key=lambda x: x[0])  # 按时间戳排序

    def get_current_time(self):
        if self.is_paused:
            return pygame.mixer.music.get_pos() / 1000.0
        else:
            return time.time() - self.music_start_time

    def update_lyric(self):
        if not self.is_paused:
            current_time = time.time() - self.music_start_time

            # 将时间格式化为分钟:秒
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            current_time_str = f"{minutes:02}:{seconds:02}"

            # 更新时间标签
            self.time_label.config(text=current_time_str)

            # 如果当前时间大于或等于歌词的时间戳，则显示该歌词
            while self.current_index < len(self.lyrics) and current_time >= self.lyrics[self.current_index][0]:
                self.label.config(text=self.lyrics[self.current_index][1])
                self.current_index += 1

            # 检查是否播放完毕
            if self.current_index >= len(self.lyrics):
                # 如果是音乐模式，等待音乐播放完毕
                if self.music_file:
                    if not pygame.mixer.music.get_busy():
                        if len(self.main_window.playlist) > 1:
                            self.destroy()
                            self.main_window.play_next()
                        else:
                            self.quit_program()
                # 如果是纯字幕模式，直接结束
                else:
                    if len(self.main_window.playlist) > 1:
                        self.destroy()
                        self.main_window.play_next()
                    else:
                        self.quit_program()
                    return  # 防止继续调用 after

        self.after(100, self.update_lyric)

    def update_display_after_time_change(self, new_time):
        # 更新当前索引
        self.current_index = 0
        for i, (time_stamp, _) in enumerate(self.lyrics):
            if time_stamp <= new_time:
                self.current_index = i + 1
            else:
                break

        # 更新显示的歌词
        if self.current_index > 0:
            self.label.config(text=self.lyrics[self.current_index - 1][1])

    def toggle_pause(self, event):
        if self.is_paused:
            if self.music_file:
                pygame.mixer.music.unpause()
            self.is_paused = False
            self.music_start_time = time.time() - self.pause_time
        else:
            if self.music_file:
                pygame.mixer.music.pause()
            self.is_paused = True
            self.pause_time = time.time() - self.music_start_time

    def rewind_1_second(self, event):
        current_time = self.get_current_time()
        new_time = max(0, current_time - 5.0)
        if self.music_file:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(start=new_time)
        self.music_start_time = time.time() - new_time
        self.update_display_after_time_change(new_time)

    def fast_forward_1_second(self, event):
        current_time = self.get_current_time()
        new_time = current_time + 5.0
        if self.music_file:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(start=new_time)
        self.music_start_time = time.time() - new_time
        self.update_display_after_time_change(new_time)

    def rewind_1_minute(self, event):
        current_time = self.get_current_time()
        new_time = max(0, current_time - 30.0)
        if self.music_file:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(start=new_time)
        self.music_start_time = time.time() - new_time
        self.update_display_after_time_change(new_time)

    def fast_forward_1_minute(self, event):
        current_time = self.get_current_time()
        new_time = current_time + 30.0
        if self.music_file:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(start=new_time)
        self.music_start_time = time.time() - new_time
        self.update_display_after_time_change(new_time)

    def on_button_press(self, event):
        # 记录鼠标按下时的位置
        self.initial_x = event.x
        self.initial_y = event.y

    def on_mouse_drag(self, event):
        # 计算鼠标拖动的距离，并更新窗口的位置
        delta_x = event.x - self.initial_x
        delta_y = event.y - self.initial_y

        # 获取当前窗口的位置
        current_x = self.winfo_x()
        current_y = self.winfo_y()

        # 更新窗口的位置
        new_x = current_x + delta_x
        new_y = current_y + delta_y
        self.geometry(f"+{new_x}+{new_y}")  # 设置新的窗口位置
        self.save_window_position()

    def save_window_position(self):
        """保存窗口位置到配置文件"""
        self.config["window"]["initial_position"]["x"] = self.winfo_x()
        self.config["window"]["initial_position"]["y"] = self.winfo_y()
        
        # 获取配置文件路径
        if getattr(sys, 'frozen', False):
            config_path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')
        else:
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
        
        # 保存配置
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)