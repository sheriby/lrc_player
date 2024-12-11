pyinstaller -F -w -i icon.ico --hidden-import=tkinter --hidden-import=pygame --hidden-import=pystray --hidden-import=PIL lrc_player.py
copy "config.json" "dist/config.json"
copy "icon.ico" "dist/icon.ico"
