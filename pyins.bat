pyinstaller -F -w --hidden-import=tkinter --hidden-import=pygame lrc_player.py
copy "config.json" "dist/config.json"
