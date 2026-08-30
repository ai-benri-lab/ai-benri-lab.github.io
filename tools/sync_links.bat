@echo off
cd /d c:\work-space\ai-benri-lab-site
set PYTHONIOENCODING=utf-8
"C:\Users\mori1\AppData\Local\Programs\Python\Python313\python.exe" tools\sync_links.py >> tools\sync_links.log 2>&1
"C:\Users\mori1\AppData\Local\Programs\Python\Python313\python.exe" tools\gen_blog.py >> tools\sync_links.log 2>&1
