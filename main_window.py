import tkinter as tk
from tkinter import filedialog, ttk
import os
import sys
import json
import pygame
from mutagen.mp3 import MP3
from lyrics_display import LyricsDisplay
from config_manager import ConfigManager

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # 加载配置文件
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        self.title("音乐播放器")
        # 使用配置文件中的窗口大小和位置
        window_geometry = (
            f"{self.config['main_window']['width']}x"
            f"{self.config['main_window']['height']}+"
            f"{self.config['main_window']['initial_position']['x']}+"
            f"{self.config['main_window']['initial_position']['y']}"
        )
        self.geometry(window_geometry)
        
        # 创建播放列表
        self.playlist = []
        self.current_index = 0
        
        # 设置窗口样式
        self.configure(bg="#f0f0f0")
        
        # 创建界面
        self.create_widgets()
        
        # 设置样式
        self._configure_style()
        
        # 绑定窗口大小和位置改变事件
        self.bind("<Configure>", self.on_window_configure)
        
        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _configure_style(self):
        style = ttk.Style()
        style.configure("Treeview", 
                       background="#ffffff",
                       foreground="#333333",
                       fieldbackground="#ffffff",
                       rowheight=35,
                       font=('微软雅黑', 11))
        
        # 设置选中项的样式
        style.map("Treeview",
                  background=[('selected', '#e6f3ff')],
                  foreground=[('selected', '#333333')])

        # 修改表头样式
        style.configure("Treeview.Heading",
                       background="#ffffff",
                       foreground="#888888",
                       font=('微软雅黑', 11, 'bold'),
                       padding=(10, 5))
        

    def create_widgets(self):
        # 创建顶部框架
        top_frame = tk.Frame(self, bg="#4a90e2")
        top_frame.pack(fill=tk.X, pady=0)
        
        # 创建按钮框架
        self._create_buttons(top_frame)
        
        # 创建播放列表
        self._create_playlist()

    def _create_buttons(self, parent):
        btn_frame = tk.Frame(parent, bg="#4a90e2")
        btn_frame.pack(pady=12)
        
        # 创建打开文件夹按钮
        self.open_folder_btn = tk.Button(btn_frame, 
                                 text="打开文件夹",
                                 font=('微软雅黑', 11),
                                 bg="#ffffff",
                                 fg="#4a90e2",
                                 relief="flat",
                                 padx=20,
                                 command=self.open_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建打开文件按钮
        self.open_file_btn = tk.Button(btn_frame,
                                text="打开文件",
                                font=('微软雅黑', 11),
                                bg="#ffffff", 
                                fg="#4a90e2",
                                relief="flat",
                                padx=20,
                                command=self.open_file)
        self.open_file_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建打开字幕按钮
        self.open_subtitle_btn = tk.Button(btn_frame,
                                text="打开字幕",
                                font=('微软雅黑', 11),
                                bg="#ffffff", 
                                fg="#4a90e2",
                                relief="flat",
                                padx=20,
                                command=self.open_subtitle)
        self.open_subtitle_btn.pack(side=tk.LEFT, padx=5)

    def _create_playlist(self):
        list_frame = tk.Frame(self, bg="#ffffff")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建树形视图
        self.tree = ttk.Treeview(list_frame, 
                                columns=("文件名", "时长"), 
                                show="headings",
                                yscrollcommand=scrollbar.set)
        
        # 设置列
        self.tree.heading("文件名", text="歌曲名称")
        self.tree.heading("时长", text="时长")
        self.tree.column("文件名", width=400)
        self.tree.column("时长", width=100, anchor="center")
        
        # 设置交替行颜色
        self.tree.tag_configure('oddrow', background='#f9f9f9')
        self.tree.tag_configure('evenrow', background='#ffffff')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        scrollbar.config(command=self.tree.yview)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.play_selected)

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.playlist.clear()
            self.tree.delete(*self.tree.get_children())
            
            # 初始化pygame mixer用于非mp3文件
            pygame.mixer.init()
            
            # 遍历文件夹中的音乐文件
            row_count = 0
            for file in os.listdir(folder_path):
                if file.endswith(('.mp3', '.wav')):
                    music_path = os.path.join(folder_path, file)
                    self.playlist.append(music_path)
                    
                    # 获取音乐时长
                    if file.endswith('.mp3'):
                        # 使用mutagen读取mp3时长
                        audio = MP3(music_path)
                        duration = audio.info.length
                    else:
                        # 其他格式用pygame读取
                        sound = pygame.mixer.Sound(music_path)
                        duration = sound.get_length()
                        
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    duration_str = f"{minutes:02d}:{seconds:02d}"
                    
                    # 去掉文件后缀显示
                    display_name = os.path.splitext(file)[0]
                    
                    # 设置交替行颜色
                    tag = 'evenrow' if row_count % 2 == 0 else 'oddrow'
                    self.tree.insert("", "end", values=(display_name, duration_str), tags=(tag,))
                    row_count += 1
            
            # 退出pygame mixer        
            pygame.mixer.quit()

    def open_file(self):
        """打开单个音乐文件"""
        file_path = filedialog.askopenfilename(filetypes=[("音频文件", "*.mp3;*.wav")])
        if file_path:
            self.playlist = [file_path]
            self.current_index = 0
            self.tree.delete(*self.tree.get_children())
            
            # 直接播放文件
            self.withdraw()
            lyrics_window = LyricsDisplay(file_path, self)
            lyrics_window.mainloop()

    def play_selected(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.current_index = self.tree.index(selected_item)
            music_file = self.playlist[self.current_index]
            # 隐藏主窗口
            self.withdraw()
            # 创建并显示歌词窗口
            lyrics_window = LyricsDisplay(music_file, self)
            lyrics_window.mainloop()

    def play_next(self):
        """播放下一首歌"""
        self.current_index += 1
        if self.current_index < len(self.playlist):
            music_file = self.playlist[self.current_index]
            lyrics_window = LyricsDisplay(music_file, self)
            lyrics_window.mainloop()
        else:
            self.destroy()  # 播放列表结束,直接退出程序


    def on_window_configure(self, event):
        """窗口大小或位置改变时的回调"""
        if event.widget == self:
            self.save_window_config()

    def on_closing(self):
        """窗口关闭时的回调"""
        self.save_window_config()
        self.quit()

    def save_window_config(self):
        """保存窗口配置"""
        # 保存窗口大小
        self.config['main_window']['width'] = self.winfo_width()
        self.config['main_window']['height'] = self.winfo_height()
        
        # 保存窗口位置
        self.config['main_window']['initial_position']['x'] = self.winfo_x()
        self.config['main_window']['initial_position']['y'] = self.winfo_y()
        
        # 保存配置到文件
        self.config_manager.save_config(self.config)
        
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
        
    def create_widgets(self):
        # 创建顶部框架
        top_frame = tk.Frame(self, bg="#4a90e2")
        top_frame.pack(fill=tk.X, pady=0)
        
        # 创建按钮框架
        btn_frame = tk.Frame(top_frame, bg="#4a90e2")
        btn_frame.pack(pady=12)
        
        # 创建打开文件夹按钮
        self.open_folder_btn = tk.Button(btn_frame, 
                                 text="打开文件夹",
                                 font=('微软雅黑', 11),
                                 bg="#ffffff",
                                 fg="#4a90e2",
                                 relief="flat",
                                 padx=20,
                                 command=self.open_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建打开文件按钮
        self.open_file_btn = tk.Button(btn_frame,
                                text="打开文件",
                                font=('微软雅黑', 11),
                                bg="#ffffff", 
                                fg="#4a90e2",
                                relief="flat",
                                padx=20,
                                command=self.open_file)
        self.open_file_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建打开字幕按钮
        self.open_subtitle_btn = tk.Button(btn_frame,
                                text="打开歌词",
                                font=('微软雅黑', 11),
                                bg="#ffffff", 
                                fg="#4a90e2",
                                relief="flat",
                                padx=20,
                                command=self.open_subtitle)
        self.open_subtitle_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建播放列表框架
        list_frame = tk.Frame(self, bg="#ffffff")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 创建播放列表
        self.tree = ttk.Treeview(list_frame, columns=("文件名", "时长"), show="headings")
        self.tree.heading("文件名", text="歌曲名称")
        self.tree.heading("时长", text="时长")
        self.tree.column("文件名", width=400)
        self.tree.column("时长", width=100, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.play_selected)
        
    def open_file(self):
        """打开单个音乐文件"""
        file_path = filedialog.askopenfilename(filetypes=[("音频文件", "*.mp3;*.wav")])
        if file_path:
            self.playlist = [file_path]
            self.current_index = 0
            self.tree.delete(*self.tree.get_children())
            
            # 直接播放文件
            self.withdraw()
            lyrics_window = LyricsDisplay(file_path, self)
            lyrics_window.mainloop()
            
    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.playlist.clear()
            self.tree.delete(*self.tree.get_children())
            
            # 初始化pygame mixer用于非mp3文件
            pygame.mixer.init()
            
            # 遍历文件夹中的音乐文件
            row_count = 0
            for file in os.listdir(folder_path):
                if file.endswith(('.mp3', '.wav')):
                    music_path = os.path.join(folder_path, file)
                    self.playlist.append(music_path)
                    
                    # 获取音乐时长
                    if file.endswith('.mp3'):
                        # 使用mutagen读取mp3时长
                        audio = MP3(music_path)
                        duration = audio.info.length
                    else:
                        # 其他格式用pygame读取
                        sound = pygame.mixer.Sound(music_path)
                        duration = sound.get_length()
                        
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    duration_str = f"{minutes:02d}:{seconds:02d}"
                    
                    # 去掉文件后缀显示
                    display_name = os.path.splitext(file)[0]
                    
                    # 设置交替行颜色
                    tag = 'evenrow' if row_count % 2 == 0 else 'oddrow'
                    self.tree.insert("", "end", values=(display_name, duration_str), tags=(tag,))
                    row_count += 1
            
            # 退出pygame mixer        
            pygame.mixer.quit()
                    
    def play_selected(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.current_index = self.tree.index(selected_item)
            music_file = self.playlist[self.current_index]
            # 隐藏主窗口
            self.withdraw()
            # 创建并显示歌词窗口
            lyrics_window = LyricsDisplay(music_file, self)
            lyrics_window.mainloop()
            
    def play_next(self):
        """播放下一首歌"""
        self.current_index += 1
        if self.current_index < len(self.playlist):
            music_file = self.playlist[self.current_index]
            lyrics_window = LyricsDisplay(music_file, self)
            lyrics_window.mainloop()
        else:
            self.quit()  # 播放列表结束,退出程序
            
    def open_subtitle(self):
        """打开字幕文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("字幕文件", "*.lrc;*.srt;*.vtt")]
        )
        if file_path:
            # 隐藏主窗口
            self.withdraw()
            # 创建并显示歌词窗口,传入None作为音乐文件
            lyrics_window = LyricsDisplay(None, self, subtitle_file=file_path)
            lyrics_window.mainloop()