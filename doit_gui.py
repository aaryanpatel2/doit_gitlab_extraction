import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import os
import sys
import datetime
import threading
import calendar
from functools import reduce
import pandas as pd

import get_gitlab_info

class GitlabInfoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GitLab Info Extractor')
        self.geometry('450x450')
        self.resizable(False, False)
        style = ttk.Style(self)
        style.theme_use(style.theme_names()[0])
        style.configure('TButton', font=('Segoe UI', 11), padding=6)
        style.configure('TLabel', font=('Segoe UI', 11))
        style.configure('TEntry', font=('Segoe UI', 11))
        style.configure('TCombobox', font=('Segoe UI', 11))
        style.configure('Vertical.TScrollbar', gripcount=0, background='#e0e0e0', darkcolor='#b0b0b0', lightcolor='#f0f0f0', troughcolor='#d0d0d0', bordercolor='#a0a0a0', arrowcolor='#404040')
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text='Project ID:').pack(pady=(20, 0), anchor='w', padx=30)
        self.project_id_var = tk.StringVar(value='6192')
        self.project_id_entry = ttk.Entry(self, textvariable=self.project_id_var)
        self.project_id_entry.pack(pady=5, padx=30, fill='x')

        # Date selection mode (Month or Date Range)
        ttk.Label(self, text='Date Selection Mode:').pack(pady=(10, 0), anchor='w', padx=30)
        self.date_mode_var = tk.StringVar(value='month')
        mode_frame = ttk.Frame(self)
        mode_frame.pack(pady=5, padx=30, fill='x')
        ttk.Radiobutton(mode_frame, text='Month', variable=self.date_mode_var, value='month', command=self.toggle_date_mode).pack(side='left', padx=(0, 15))
        ttk.Radiobutton(mode_frame, text='Date Range', variable=self.date_mode_var, value='range', command=self.toggle_date_mode).pack(side='left')

        # Month selection (Year and Month Comboboxes)
        self.month_label = ttk.Label(self, text='Select Year and Month:')
        self.month_label.pack(pady=(10, 0), anchor='w', padx=30)
        self.month_frame = ttk.Frame(self)
        self.month_frame.pack(pady=5, padx=30, fill='x')
        
        # Year Combobox
        current_year = datetime.datetime.now().year
        years = [str(y) for y in range(current_year - 5, current_year + 2)]
        self.year_var = tk.StringVar(value=str(current_year))
        ttk.Label(self.month_frame, text='Year:').pack(side='left', padx=(0, 5))
        self.year_combo = ttk.Combobox(self.month_frame, textvariable=self.year_var, values=years, width=6, state='normal')
        self.year_combo.pack(side='left', padx=(0, 15))
        
        # Month Combobox
        months = [f'{m:02d}' for m in range(1, 13)]
        self.month_var = tk.StringVar(value=f'{datetime.datetime.now().month:02d}')
        ttk.Label(self.month_frame, text='Month:').pack(side='left', padx=(0, 5))
        self.month_combo = ttk.Combobox(self.month_frame, textvariable=self.month_var, values=months, width=4, state='normal')
        self.month_combo.pack(side='left')

        # Date Range selection
        self.range_label = ttk.Label(self, text='Select Date Range:')
        self.range_frame = ttk.Frame(self)
        
        # Start Date
        start_frame = ttk.Frame(self.range_frame)
        start_frame.pack(pady=2, fill='x')
        ttk.Label(start_frame, text='From:').pack(side='left', padx=(0, 5))
        self.start_date = DateEntry(start_frame, width=18, borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.pack(side='left', padx=(0, 10))
        self.start_date.bind('<<DateEntrySelected>>', self.on_start_date_changed)
        
        # End Date
        end_frame = ttk.Frame(self.range_frame)
        end_frame.pack(pady=2, fill='x')
        ttk.Label(end_frame, text='To:').pack(side='left', padx=(0, 5))
        self.end_date = DateEntry(end_frame, width=18, borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.pack(side='left', padx=(0, 10))
        self.end_date.bind('<<DateEntrySelected>>', self.on_end_date_changed)

        # Output directory
        self.output_dir_label = ttk.Label(self, text='Output Directory:')
        self.output_dir_label.pack(pady=(10, 0), anchor='w', padx=30)
        self.output_dir_var = tk.StringVar(value=os.getcwd())  # Pre-fill with current working directory
        self.output_dir_entry = ttk.Entry(self, textvariable=self.output_dir_var, width=30)
        self.output_dir_entry.pack(pady=5, padx=30, fill='x')
        ttk.Button(self, text='Browse...', command=self.browse_output_dir, style='Accent.TButton').pack(pady=2, padx=30, anchor='w')

        # Run button
        self.run_button = ttk.Button(self, text='Extract Data', command=self.run_extraction, style='Accent.TButton')
        self.run_button.pack(pady=(20, 5), padx=30, fill='x')

        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground='blue')
        self.status_label.pack(pady=(0, 15), padx=30, anchor='w')
        
        # Initialize with month mode visible
        self.toggle_date_mode()

    def toggle_date_mode(self):
        """Toggle between month and date range selection modes"""
        mode = self.date_mode_var.get()
        if mode == 'month':
            # Show month selection, hide date range
            self.month_label.pack(pady=(10, 0), anchor='w', padx=30, before=self.output_dir_label)
            self.month_frame.pack(pady=5, padx=30, fill='x', before=self.output_dir_label)
            self.range_label.pack_forget()
            self.range_frame.pack_forget()
        else:
            # Show date range, hide month selection
            self.month_label.pack_forget()
            self.month_frame.pack_forget()
            self.range_label.pack(pady=(10, 0), anchor='w', padx=30, before=self.output_dir_label)
            self.range_frame.pack(pady=5, padx=30, fill='x', before=self.output_dir_label)

    def on_start_date_changed(self, event):
        """Ensure start date is not after end date"""
        if self.start_date.get_date() > self.end_date.get_date():
            self.end_date.set_date(self.start_date.get_date())
    
    def on_end_date_changed(self, event):
        """Ensure end date is not before start date"""
        if self.end_date.get_date() < self.start_date.get_date():
            self.start_date.set_date(self.end_date.get_date())

    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)

    def run_extraction(self):
        project_id = self.project_id_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        mode = self.date_mode_var.get()

        if not project_id or not output_dir:
            messagebox.showerror('Error', 'Please fill in all fields.')
            return

        # Disable the button during extraction
        self.run_button.config(state='disabled')
        self.status_var.set('Running extraction...')
        self.update_idletasks()

        # Run extraction in a separate thread to keep UI responsive
        def extraction_thread():
            try:
                # Determine date range based on mode
                if mode == 'month':
                    year = int(self.year_var.get())
                    month = int(self.month_var.get())
                    since = datetime.datetime(year, month, 1)
                    last_day = calendar.monthrange(year, month)[1]
                    until = datetime.datetime(year, month, last_day, 23, 59, 59)
                else:
                    since = self.start_date.get_date()
                    until = self.end_date.get_date()
                    since = datetime.datetime.combine(since, datetime.time.min)
                    until = datetime.datetime.combine(until, datetime.time.max)

                # Fetch all data using imported functions with progress updates
                self.after(0, lambda: self.status_var.set('Fetching push events...'))
                push_events = get_gitlab_info.get_push_events(project_id, since, until)

                self.after(0, lambda: self.status_var.set('Fetching commits...'))
                commits = get_gitlab_info.get_commits(project_id, since, until)

                self.after(0, lambda: self.status_var.set('Fetching merge requests...'))
                merge_events = get_gitlab_info.get_merge_events(project_id)

                self.after(0, lambda: self.status_var.set('Fetching issues...'))
                issue_events = get_gitlab_info.get_issue_events(project_id, since, until)

                self.after(0, lambda: self.status_var.set('Fetching milestones...'))
                milestones = get_gitlab_info.get_milestones(project_id, since, until)

                # Use the new unified Excel output function
                self.after(0, lambda: self.status_var.set('Saving Excel files...'))
                merged_output_file, commits_output_file, output_dir_final = get_gitlab_info.save_gitlab_data_to_excel(
                    push_events, commits, merge_events, issue_events, milestones, since, until, output_dir
                )
                self.after(0, lambda: self.extraction_complete(output_dir_final))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self.extraction_failed(error_msg))

        thread = threading.Thread(target=extraction_thread)
        thread.daemon = True
        thread.start()
    
    def extraction_complete(self, output_path):
        self.status_var.set('Extraction complete!')
        self.run_button.config(state='normal')
        success_msg = f'Data extraction complete!\n\nFiles saved to:\n{output_path}'
        messagebox.showinfo('Success', success_msg)
    
    def extraction_failed(self, error_msg):
        self.status_var.set('Extraction failed.')
        self.run_button.config(state='normal')
        messagebox.showerror('Error', f'Extraction failed!\n\nError: {error_msg}')

if __name__ == '__main__':
    try:
        import tkcalendar
    except ImportError:
        messagebox.showerror('Missing Dependency', 'tkcalendar is required. Install it with:\npip install tkcalendar')
        sys.exit(1)
    try:
        app = GitlabInfoApp()
        app.mainloop()
    except Exception as e:
        import traceback
        error_message = f"ERROR: {e}\n{traceback.format_exc()}"
        # Write error to a log file in the same directory as the executable
        try:
            with open("doit_gui_error.log", "w") as f:
                f.write(error_message)
        except Exception:
            pass
        # Also try to show a message box if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", error_message)
            root.destroy()
        except Exception:
            pass
