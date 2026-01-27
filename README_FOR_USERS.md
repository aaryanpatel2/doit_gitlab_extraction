**Prerequisite for Students**: Make sure you are signed in as system administrator. If you do not have access to that specific account, contact DoIT or Nathan for further assistance and setup.

1. **Copy the Project Folder**
   - Transfer the entire project folder (including `doit_gui.py`, `get_gitlab_info.py`, `.env`, and this README) to a Windows computer.

2. **Install Python (if not already installed)**
   - Download Python from https://www.python.org/downloads/windows/
   - During installation, check the box that says "Add Python to PATH".

3. **Install Required Packages**
   - Open Command Prompt (press Windows key, type `cmd`, and press Enter).
   - Run the following command:
     ```
     pip install pyinstaller tkcalendar pandas requests python-dotenv openpyxl
     ```

4. **Build the Executable**
   - In Command Prompt, navigate to your project folder. For example:
     ```
     cd C:\Users\YourName\Downloads\DoIT_GitLab_Info
     ```
   - Run:
     ```
     python -m PyInstaller --onefile --windowed --add-data ".env;." doit_gui.py
     ```
   - When finished, you will find `doit_gui.exe` in the `dist` folder inside your project folder.

5. **Open the App**
   - Double-click `doit_gui.exe`. OR `cd dist` and run '.\doit_gui.exe'
   - If you see a security warning, click "More info" and then "Run anyway".
   - You can also right click on application icon and pin it to taskbar and run it without worrying about commands!

6. **Fill Out the Form**
   - Enter the **Project ID** (ask your admin if you don't know it).
   - Select the **Year** and **Month** you want data for.
   - Click **Browse...** and choose where you want the Excel files to be saved.

7. **Extract Data**
   - Click the **Extract Data** button.
   - Wait for the process to finish. You will see a message when it's done.
   - The Excel files will appear in the folder you selected.

## Troubleshooting

- If you see a warning from Windows Defender, click "More info" and then "Run anyway".
- If the app doesn't open, make sure you are running `doit_gui.exe` from inside the folder.
- If you get an error about missing files, make sure `.env` and `get_gitlab_info.py` are in the same folder as `doit_gui.exe`.
