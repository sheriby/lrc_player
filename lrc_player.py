import tkinter as tk
import time
from datetime import timedelta
import re
import json
import ctypes
import os
import sys
from lrc_srt_convert import convert
from vtt2srt import vtt_to_srt

# 解析 LRC 文件
def parse_lrc_file(file_path):
    lyrics = []
    lrc_regex = r'\[(\d{2}):(\d{2}\.\d{2})\](.*)'

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.match(lrc_regex, line.strip())
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                lyric = match.group(3)
                timestamp = timedelta(minutes=minutes, seconds=seconds)
                lyrics.append((timestamp, lyric))

    return lyrics

# 显示歌词的窗口
class LyricsDisplay(tk.Tk):
    def __init__(self):
        super().__init__()

        # 读取配置文件
        self.config = self.load_config()
        
        self.lyrics = self.load_lyrics(self.config["lyrics_file"])
        self.current_index = 0


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
        # self.attributes("-transparentcolor", "white")
        self.attributes("-alpha", 0.4)

        # 设置无边框窗体
        self.overrideredirect(True)
        self.geometry(f"{self.window_width}x{self.window_height}+{self.initial_x}+{self.initial_y}")
        self.configure(bg="black")

        # 时间标签，用于显示当前时间
        self.time_label = tk.Label(self, font=(self.time_font_family, self.time_font_size), fg=self.time_font_color, bg="black")
        self.time_label.pack(fill=tk.X, side=tk.TOP)  # 设置上方和下方的间距

        # 歌词标签，用于显示歌词
        self.label = tk.Label(self, font=(self.font_family, self.font_size), fg=self.font_color, bg="black", anchor="center")
        self.label.pack(fill=tk.BOTH)

        # 初始位置
        self.initial_x = 0
        self.initial_y = 0

        # 绑定鼠标事件到container上，使整个背景区域都可以拖动
        self.bind("<ButtonPress-1>", self.on_button_press)
        self.bind("<B1-Motion>", self.on_mouse_drag)

        # 绑定键盘事件
        self.bind("<Left>", self.rewind_1_second)  # 左箭头回退1秒
        self.bind("<Right>", self.fast_forward_1_second)  # 右箭头快进1秒
        self.bind("<Control-c>", self.quit_program)  # 绑定 Ctrl+C 退出程序

        self.start_time = time.time()  # 记录程序开始的时间
        self.after(100, self.update_lyric)  # 每 100 毫秒更新一次歌词
    
    def quit_program(self, event=None):
        """ 退出程序 """
        self.quit()  # 退出Tkinter事件循环
        self.destroy()  # 销毁窗口
    
    def load_config(self):
        # 获取当前程序所在的目录
        if getattr(sys, 'frozen', False):
            # 获取打包后的程序路径
            config_path = os.path.join(os.path.dirname(sys.argv[0]), 'config.json')
        else:
            # 如果是未打包的脚本，配置文件在当前工作目录下
            config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

        # 确保配置文件路径正确
        print(f"Looking for config file at: {config_path}")
        
        # 读取配置文件
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"Error: {config_path} not found!")
            return None

        return config


    def load_lyrics(self, lyrics_file):
        # 读取歌词文件，返回歌词的时间和文本

        if lyrics_file.split(".")[len(lyrics_file.split("."))-1] == "vtt":
            vtt_to_srt(lyrics_file)
            lyrics_file = lyrics_file.replace(".vtt", ".srt")

        if lyrics_file.split(".")[len(lyrics_file.split("."))-1] == "srt":
            output_file = lyrics_file.replace(".srt", ".lrc")
            convert(lyrics_file, output_file)
            lyrics_file = output_file

        lyrics = []
        with open(lyrics_file, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip():
                    time_str, text = line.split(']')  # 获取时间戳和歌词文本
                    time_str = time_str.strip('[')  # 去除 '['
                    minutes, seconds = map(float, time_str.split(':'))
                    time_in_seconds = minutes * 60 + seconds  # 转换为秒
                    lyrics.append((time_in_seconds, text.strip()))
        return lyrics

    def update_lyric(self):
        # 计算当前播放时间（从 0 开始计时）
        current_time = time.time() - self.start_time  # 直接获取浮动秒数

        # 将时间格式化为分钟:秒
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        current_time_str = f"{minutes:02}:{seconds:02}"  # 格式化为 mm:ss

        # 更新时间标签
        self.time_label.config(text=current_time_str)

        # 如果当前时间大于或等于歌词的时间戳，则显示该歌词
        while self.current_index < len(self.lyrics) and current_time >= self.lyrics[self.current_index][0]:
            self.label.config(text=self.lyrics[self.current_index][1])
            self.current_index += 1

        # 如果所有歌词显示完毕，退出程序
        if self.current_index >= len(self.lyrics):
            self.quit()

        self.after(100, self.update_lyric)  # 继续更新歌词

    def update_display_after_time_change(self, is_rewind):
        # 重新计算当前时间
        current_time = time.time() - self.start_time  # 直接获取浮动秒数

        # 将时间格式化为分钟:秒
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        current_time_str = f"{minutes:02}:{seconds:02}"  # 格式化为 mm:ss

        # 更新时间标签
        self.time_label.config(text=current_time_str)

        if is_rewind:
            # 如果是回退1秒，遍历前面的歌词并显示最近的一条歌词
            while self.current_index > 0 and current_time < self.lyrics[self.current_index][0]:
                self.current_index -= 1
        else:
            # 如果是快进1秒，增加 current_index 并显示后面的歌词
            while self.current_index < len(self.lyrics) and current_time >= self.lyrics[self.current_index][0]:
                self.current_index += 1

        # 更新歌词显示
        if self.current_index > 0:
            self.label.config(text=self.lyrics[self.current_index - 1][1])

    def rewind_1_second(self, event):
        # 向前回退1秒
        self.start_time += 1  
        self.update_display_after_time_change(is_rewind=True)  # 更新歌词显示

    def fast_forward_1_second(self, event):
        # 向前快进1秒
        self.start_time -= 1  
        self.update_display_after_time_change(is_rewind=False)  # 更新歌词显示

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


# 主函数
def main():
    # 创建并显示歌词窗口
    app = LyricsDisplay()
    app.mainloop()

if __name__ == "__main__":
    main()
