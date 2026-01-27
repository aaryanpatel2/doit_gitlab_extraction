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
        
        # End Date
        end_frame = ttk.Frame(self.range_frame)
        end_frame.pack(pady=2, fill='x')
        ttk.Label(end_frame, text='To:').pack(side='left', padx=(0, 5))
        self.end_date = DateEntry(end_frame, width=18, borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.pack(side='left', padx=(0, 10))

        # Output directory
        self.output_dir_label = ttk.Label(self, text='Output Directory:')
        self.output_dir_label.pack(pady=(10, 0), anchor='w', padx=30)
        self.output_dir_var = tk.StringVar()
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
                    year = self.year_var.get().strip()
                    month = self.month_var.get().strip()
                    if not year or not month:
                        self.after(0, lambda: messagebox.showerror('Error', 'Please select year and month.'))
                        self.after(0, lambda: self.run_button.config(state='normal'))
                        return
                    year_int, month_int = int(year), int(month)
                    since = datetime.datetime(year_int, month_int, 1)
                    last_day = calendar.monthrange(year_int, month_int)[1]
                    until = datetime.datetime(year_int, month_int, last_day, 23, 59, 59)
                else:  # date range mode
                    since = datetime.datetime.combine(self.start_date.get_date(), datetime.time.min)
                    until = datetime.datetime.combine(self.end_date.get_date(), datetime.time(23, 59, 59))
                    if since > until:
                        self.after(0, lambda: messagebox.showerror('Error', 'Start date must be before or equal to end date.'))
                        self.after(0, lambda: self.run_button.config(state='normal'))
                        return
                
                # Fetch all data using imported functions with progress updates
                self.after(0, lambda: self.status_var.set('Fetching push events...'))
                push_events = get_gitlab_info.get_push_events(project_id, since, until)
                
                self.after(0, lambda: self.status_var.set('Fetching commits...'))
                commits = get_gitlab_info.get_commits(project_id, since, until)
                print(f"DEBUG: Fetched {len(commits) if isinstance(commits, list) else 0} commits")
                
                self.after(0, lambda: self.status_var.set('Fetching merge requests...'))
                merge_events = get_gitlab_info.get_merge_events(project_id)
                merge_events_opened = get_gitlab_info.get_merge_events_opened(project_id)
                merge_events_closed = get_gitlab_info.get_merge_events_closed(project_id)
                merge_events_merged = get_gitlab_info.get_merge_events_merged(project_id)
                
                self.after(0, lambda: self.status_var.set('Fetching issues...'))
                issue_events = get_gitlab_info.get_issue_events(project_id, since, until)
                closed_issues = get_gitlab_info.get_closed_issues(project_id, since, until)
                bug_issues = get_gitlab_info.get_bug_issues(project_id, since, until)
                
                self.after(0, lambda: self.status_var.set('Fetching milestones and service desk...'))
                milestones = get_gitlab_info.get_milestones(project_id, since, until)
                service_desk_issues = get_gitlab_info.get_service_desk_issues(project_id, since, until)
                
                # Filter and process data
                self.after(0, lambda: self.status_var.set('Filtering milestones...'))
                import pandas as pd
                milestones_in_month = []
                for milestone in milestones:
                    created_at_str = milestone.get("created_at")
                    if created_at_str:
                        created_at = pd.to_datetime(created_at_str, utc=True).tz_localize(None)
                        since_naive = since.replace(tzinfo=None)
                        until_naive = until.replace(tzinfo=None)
                        if since_naive <= created_at <= until_naive:
                            milestones_in_month.append(milestone)
                
                # Convert to DataFrames
                self.after(0, lambda: self.status_var.set('Converting to data tables...'))
                push_df = pd.DataFrame(push_events) if isinstance(push_events, list) else pd.DataFrame()
                commits_df = pd.DataFrame(commits) if isinstance(commits, list) else pd.DataFrame()
                print(f"DEBUG: Commits DataFrame has {len(commits_df)} rows and {len(commits_df.columns)} columns")
                if not commits_df.empty:
                    print(f"DEBUG: Commits columns: {list(commits_df.columns)}")
                merge_df = pd.DataFrame(merge_events) if isinstance(merge_events, list) else pd.DataFrame()
                merge_df_opened = pd.DataFrame(merge_events_opened) if isinstance(merge_events_opened, list) else pd.DataFrame()
                merge_df_closed = pd.DataFrame(merge_events_closed) if isinstance(merge_events_closed, list) else pd.DataFrame()
                merge_df_merged = pd.DataFrame(merge_events_merged) if isinstance(merge_events_merged, list) else pd.DataFrame()
                issue_df = pd.DataFrame(issue_events) if isinstance(issue_events, list) else pd.DataFrame()
                milestones_df = pd.DataFrame(milestones_in_month) if isinstance(milestones_in_month, list) else pd.DataFrame()
                service_desk_df = pd.DataFrame(service_desk_issues) if isinstance(service_desk_issues, list) else pd.DataFrame()
                closed_issues_df = pd.DataFrame(closed_issues) if isinstance(closed_issues, list) else pd.DataFrame()
                bug_issues_df = pd.DataFrame(bug_issues) if isinstance(bug_issues, list) else pd.DataFrame()
                
                # Filter and clean data
                def filter_by_date(df, since, until, date_column='created_at'):
                    if df.empty or date_column not in df.columns:
                        return df
                    df[date_column] = pd.to_datetime(df[date_column], errors='coerce', utc=True)
                    since_utc = pd.to_datetime(since).tz_localize('UTC')
                    until_utc = pd.to_datetime(until).tz_localize('UTC')
                    filtered_df = df[(df[date_column] >= since_utc) & (df[date_column] <= until_utc)]
                    if date_column in filtered_df.columns:
                        filtered_df = filtered_df.copy()
                        filtered_df[date_column] = filtered_df[date_column].dt.tz_convert('UTC').dt.tz_localize(None)
                    return filtered_df
                
                def remove_timezone_info(df):
                    if df.empty:
                        return df
                    df_copy = df.copy()
                    for col in df_copy.columns:
                        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                            if hasattr(df_copy[col].dtype, 'tz') and df_copy[col].dtype.tz is not None:
                                df_copy[col] = df_copy[col].dt.tz_convert('UTC').dt.tz_localize(None)
                            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    return df_copy
                
                # Filter merge DataFrames
                self.after(0, lambda: self.status_var.set('Filtering merge requests by date...'))
                filtered_merge_df = filter_by_date(merge_df.copy(), since, until)
                filtered_merge_df_opened = filter_by_date(merge_df_opened.copy(), since, until)
                filtered_merge_df_closed = filter_by_date(merge_df_closed.copy(), since, until)
                filtered_merge_df_merged = filter_by_date(merge_df_merged.copy(), since, until)
                filtered_issue_df = filter_by_date(issue_df.copy(), since, until, 'updated_at') if 'updated_at' in issue_df.columns else issue_df
                
                # Remove timezone info
                self.after(0, lambda: self.status_var.set('Cleaning data...'))
                push_df_clean = remove_timezone_info(push_df)
                commits_df_clean = remove_timezone_info(commits_df)
                filtered_merge_df_clean = remove_timezone_info(filtered_merge_df)
                filtered_merge_df_opened_clean = remove_timezone_info(filtered_merge_df_opened)
                filtered_merge_df_closed_clean = remove_timezone_info(filtered_merge_df_closed)
                filtered_merge_df_merged_clean = remove_timezone_info(filtered_merge_df_merged)
                filtered_issue_df_clean = remove_timezone_info(filtered_issue_df)
                service_desk_df_clean = remove_timezone_info(service_desk_df)
                milestones_df_clean = remove_timezone_info(milestones_df)
                closed_issues_df_clean = remove_timezone_info(closed_issues_df)
                bug_issues_df_clean = remove_timezone_info(bug_issues_df)
                
                # Merge DataFrames
                self.after(0, lambda: self.status_var.set('Merging all data...'))
                def merge_on_project_id(left, right):
                    right_unique = right[[col for col in right.columns if col not in left.columns or col == 'project_id']]
                    return pd.merge(left, right_unique, on='project_id', how='outer')
                
                dfs_to_merge = [
                    df for df in [
                        push_df_clean, filtered_merge_df_clean, filtered_merge_df_opened_clean,
                        filtered_merge_df_closed_clean, filtered_merge_df_merged_clean,
                        filtered_issue_df_clean, milestones_df_clean, service_desk_df_clean,
                        closed_issues_df_clean, bug_issues_df_clean
                    ] if not df.empty and 'project_id' in df.columns
                ]
                
                if dfs_to_merge:
                    merged_df = reduce(merge_on_project_id, dfs_to_merge)
                else:
                    merged_df = pd.DataFrame()
                
                # Create output directory and file prefix based on mode
                if mode == 'month':
                    date_prefix = since.strftime('%Y-%m')
                else:
                    date_prefix = f"{since.strftime('%Y-%m-%d')}_to_{until.strftime('%Y-%m-%d')}"
                
                final_output_dir = os.path.join(output_dir, date_prefix)
                os.makedirs(final_output_dir, exist_ok=True)
                
                # Save to Excel
                self.after(0, lambda: self.status_var.set('Saving to Excel files...'))
                merged_output_file = os.path.join(final_output_dir, f"{date_prefix}_all_gitlab_info.xlsx")
                merged_df.to_excel(merged_output_file, index=False)
                
                commits_output_file = os.path.join(final_output_dir, f"{date_prefix}_commits.xlsx")
                print(f"DEBUG: Saving commits file with {len(commits_df_clean)} rows")
                commits_df_clean.to_excel(commits_output_file, index=False)
                
                # Update UI on main thread
                self.after(0, lambda: self.extraction_complete(final_output_dir))
                
            except Exception as e:
                # Else, Update UI on main thread with error
                self.after(0, lambda: self.extraction_failed(str(e)))
        
        # Start the extraction in a background thread
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
