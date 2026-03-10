import os
import requests
from dotenv import load_dotenv
import pandas as pd
import datetime
import sys
import calendar
from functools import reduce
from pathlib import Path

# Load environment variables
# Handle both development and PyInstaller bundled app
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = Path(sys.executable).parent
else:
    # Running in normal Python environment
    bundle_dir = Path(__file__).parent


## UNCOMMENT TO WORK ON WINDOWS
if getattr(sys, 'frozen', False):
    bundle_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
else:
    bundle_dir = Path(__file__).parent

env_path = bundle_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
GITLAB_API_URL = "https://git.doit.wisc.edu/api/v4/projects"
PRIVATE_TOKEN = os.getenv("GITLAB_DOIT_PERSONAL_ACCESS_TOKEN")

if not PRIVATE_TOKEN:
    raise ValueError(f"GITLAB_DOIT_PERSONAL_ACCESS_TOKEN is not set. Looking for .env at: {env_path}")

HEADERS = {
    "PRIVATE-TOKEN": PRIVATE_TOKEN
}

# Fetch events with error handling and pagination
def fetch_events(url, params, paginate=False):
    if not paginate:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")
        return response.json()
    
    # Handle pagination for large datasets
    all_results = []
    page = 1
    params = params.copy()
    params['per_page'] = 100
    
    print(f"DEBUG: Fetching with pagination from URL with params: {params}")
    
    while True:
        params['page'] = page
        response = requests.get(url, headers=HEADERS, params=params)
        print(f"DEBUG: Page {page} - Status: {response.status_code}")
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")
        
        results = response.json()
        print(f"DEBUG: Page {page} - Got {len(results)} items")
        if not results:
            break
        
        all_results.extend(results)
        
        # Check if there are more pages
        if 'x-next-page' not in response.headers or not response.headers['x-next-page']:
            break
        
        page += 1
    
    print(f"DEBUG: Total items fetched: {len(all_results)}")
    return all_results

# Push Events
def get_push_events(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/events"
    params = {"action": "pushed", "after": since.isoformat(), "before": until.isoformat()}
    return fetch_events(url, params, paginate=True)

# Commits
def get_commits(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/repository/commits"
    params = {"since": since.isoformat(), "until": until.isoformat()}
    print(f"DEBUG: Fetching commits from {url}")
    print(f"DEBUG: Params: {params}")
    result = fetch_events(url, params, paginate=True)
    print(f"DEBUG: Got {len(result) if isinstance(result, list) else 0} commits")
    return result

# Merge Events
def get_merge_events(project_id):
    url = f"{GITLAB_API_URL}/{project_id}/merge_requests"
    params = {"state": "all"}
    return fetch_events(url, params, paginate=True)

def get_merge_events_opened(project_id):
    url = f"{GITLAB_API_URL}/{project_id}/merge_requests"
    params = {"state": "opened"}
    return fetch_events(url, params, paginate=True)

def get_merge_events_closed(project_id):
    url = f"{GITLAB_API_URL}/{project_id}/merge_requests"
    params = {"state": "closed"}
    return fetch_events(url, params, paginate=True)

def get_merge_events_merged(project_id):
    url = f"{GITLAB_API_URL}/{project_id}/merge_requests"
    params = {"state": "merged"}
    return fetch_events(url, params, paginate=True)

# Issue Events
def get_issue_events(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/issues"
    params = {"updated_after": since.isoformat(), "updated_before": until.isoformat(), "scope": "all"}
    return fetch_events(url, params, paginate=True)

def get_closed_issues(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/issues"
    params = {
        "state": "closed",
        "updated_after": since.isoformat(),
        "updated_before": until.isoformat(),
        "scope": "all"
    }
    return fetch_events(url, params, paginate=True)

# Milestones
def get_milestones(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/milestones"
    params = {"created_after": since.isoformat(), "created_before": until.isoformat()}
    return fetch_events(url, params, paginate=True)

# Service Desk
def get_service_desk_issues(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/issues"
    params = {"created_after": since.isoformat(), "created_before": until.isoformat(), "service_desk_reply": "true", "scope": "all"}
    return fetch_events(url, params, paginate=True)

def parse_year_month(year_month_str):
    """Parse year-month string like '2025-05' and return start and end dates for that month"""
    try:
        year, month = map(int, year_month_str.split('-'))
        
        # First day of the month
        since = datetime.datetime(year, month, 1)
        
        # Last day of the month
        last_day = calendar.monthrange(year, month)[1]
        until = datetime.datetime(year, month, last_day, 23, 59, 59)
        
        return since, until
    except (ValueError, IndexError):
        raise ValueError(f"Invalid year-month format: {year_month_str}. Expected format: YYYY-MM (e.g., 2025-05)")
    
def get_bug_issues(project_id, since, until):
    url = f"{GITLAB_API_URL}/{project_id}/issues"
    params = {
        "labels": "bug",
        "created_after": since.isoformat(),
        "created_before": until.isoformat(),
        "scope": "all"
    }
    return fetch_events(url, params, paginate=True)

def save_gitlab_data_to_excel(push_events, commits, merge_events, issue_events, milestones, since, until, output_base_dir):
    """Save GitLab data to Excel files with proper filtering and deduplication"""
    import pandas as pd
    import os
    
    # Filter milestones in month
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
    push_df = pd.DataFrame(push_events) if isinstance(push_events, list) else pd.DataFrame()
    commits_df = pd.DataFrame(commits) if isinstance(commits, list) else pd.DataFrame()
    merge_df = pd.DataFrame(merge_events) if isinstance(merge_events, list) else pd.DataFrame()
    issue_df = pd.DataFrame(issue_events) if isinstance(issue_events, list) else pd.DataFrame()
    milestones_df = pd.DataFrame(milestones_in_month) if isinstance(milestones_in_month, list) else pd.DataFrame()

    # Function to filter dataframe by created_at
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

    # Function to remove timezone info from all datetime columns for Excel compatibility
    def remove_timezone_info(df):
        if df.empty:
            return df
        df_copy = df.copy()
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                if hasattr(df_copy[col].dtype, 'tz') and df_copy[col].dtype.tz is not None:
                    df_copy[col] = df_copy[col].dt.tz_convert('UTC').dt.tz_localize(None)
                # Convert to string for Excel
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        return df_copy

    # Filter merge DataFrames (these don't have date filters in API, so filter manually)
    filtered_merge_df = filter_by_date(merge_df.copy(), since, until)
    # Filter issue events by updated_at if available
    filtered_issue_df = filter_by_date(issue_df.copy(), since, until, 'updated_at') if 'updated_at' in issue_df.columns else issue_df

    # Remove timezone info from all DataFrames before saving to Excel
    push_df_clean = remove_timezone_info(push_df)
    commits_df_clean = remove_timezone_info(commits_df)
    filtered_merge_df_clean = remove_timezone_info(filtered_merge_df)
    filtered_issue_df_clean = remove_timezone_info(filtered_issue_df)
    milestones_df_clean = remove_timezone_info(milestones_df)

    # Create filename prefix with year-month
    year_month_prefix = since.strftime('%Y-%m')

    # Create output directory if it doesn't exist
    output_dir = os.path.join(output_base_dir, year_month_prefix)
    os.makedirs(output_dir, exist_ok=True)

    # Add event type identifiers and rename ID columns to avoid conflicts
    all_events = []
    
    if not push_df_clean.empty:
        push_df_clean['event_type'] = 'push'
        push_df_clean.rename(columns={'id': 'event_id'}, inplace=True)
        all_events.append(push_df_clean)
    
    if not filtered_merge_df_clean.empty:
        filtered_merge_df_clean['event_type'] = 'merge_request'
        filtered_merge_df_clean.rename(columns={'id': 'merge_request_id'}, inplace=True)
        all_events.append(filtered_merge_df_clean)
    
    if not filtered_issue_df_clean.empty:
        filtered_issue_df_clean['event_type'] = 'issue'
        filtered_issue_df_clean.rename(columns={'id': 'issue_id'}, inplace=True)
        all_events.append(filtered_issue_df_clean)
    
    if not milestones_df_clean.empty:
        milestones_df_clean['event_type'] = 'milestone'
        milestones_df_clean.rename(columns={'id': 'milestone_id'}, inplace=True)
        all_events.append(milestones_df_clean)
    
    # Concatenate all events vertically (no duplicates)
    if all_events:
        merged_df = pd.concat(all_events, axis=0, ignore_index=True)
        # Handle unhashable columns before drop_duplicates
        try:
            merged_df = merged_df.drop_duplicates()
        except TypeError:
            # If there are unhashable columns (dicts, lists), convert them to strings first
            for col in merged_df.columns:
                if merged_df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                    merged_df[col] = merged_df[col].astype(str)
            merged_df = merged_df.drop_duplicates()
    else:
        merged_df = pd.DataFrame()

    # Reorder columns in desired order
    desired_column_order = [
        'event_type', 'project_id', 'event_id', 'merge_request_id', 'issue_id', 'iid', 'title', 'description', 
        'state', 'author', 'created_at', 'updated_at', 'closed_at', 'merged_at', 'due_date', 'labels', 
        'assignees', 'assignee', 'web_url', 'action_name', 'target_id', 'target_iid', 'target_type', 
        'author_id', 'target_title', 'imported', 'imported_from', 'push_data', 'author_username', 
        'merged_by', 'merge_user', 'closed_by', 'target_branch', 'source_branch', 'user_notes_count', 
        'upvotes', 'downvotes', 'reviewers', 'source_project_id', 'target_project_id', 'draft', 
        'work_in_progress', 'milestone', 'merge_when_pipeline_succeeds', 'merge_status', 
        'detailed_merge_status', 'merge_after', 'sha', 'merge_commit_sha', 'squash_commit_sha', 
        'discussion_locked', 'should_remove_source_branch', 'force_remove_source_branch', 'prepared_at', 
        'reference', 'references', 'time_stats', 'squash', 'squash_on_merge', 'task_completion_status', 
        'has_conflicts', 'blocking_discussions_resolved', 'approvals_before_merge', 'type', 
        'merge_requests_count', 'confidential', 'issue_type', 'weight', 'blocking_issues_count', 
        'has_tasks', 'task_status', '_links', 'severity', 'moved_to_id', 'service_desk_reply_to', 
        'epic_iid', 'epic', 'iteration', 'health_status'
    ]
    
    if not merged_df.empty:
        # Only reorder columns that exist in the DataFrame
        existing_columns = [col for col in desired_column_order if col in merged_df.columns]
        remaining_columns = [col for col in merged_df.columns if col not in desired_column_order]
        final_column_order = existing_columns + remaining_columns
        merged_df = merged_df[final_column_order]

    # Write merged data (all except commits) to one file
    merged_output_file = os.path.join(output_dir, f"{year_month_prefix}_all_gitlab_info.xlsx")
    merged_df.to_excel(merged_output_file, index=False)

    # Write commits to a separate file
    commits_output_file = os.path.join(output_dir, f"{year_month_prefix}_commits.xlsx")
    commits_df_clean.to_excel(commits_output_file, index=False)

    return merged_output_file, commits_output_file, output_dir


if __name__ == "__main__":
    # Parse command line arguments
    # Usage: python get_gitlab_info.py <year-month> [project_id] [output_base_dir]
    project_id = "6192"  # default
    output_base_dir = os.getcwd()  # default
    
    if len(sys.argv) > 1:
        year_month_str = sys.argv[1]
        try:
            since, until = parse_year_month(year_month_str)
            print(f"Filtering data for {year_month_str}: {since.strftime('%Y-%m-%d')} to {until.strftime('%Y-%m-%d')}")
        except ValueError as e:
            print(f"Error: {e}")
            print("Usage: python get_gitlab_info.py <year-month> [project_id] [output_dir]")
            sys.exit(1)
    else:
        # Default to current month
        now = datetime.datetime.now()
        since = datetime.datetime(now.year, now.month, 1)
        last_day = calendar.monthrange(now.year, now.month)[1]
        until = datetime.datetime(now.year, now.month, last_day, 23, 59, 59)
        print(f"No month specified, using current month: {since.strftime('%Y-%m-%d')} to {until.strftime('%Y-%m-%d')}")
    
    # Get project_id from command line if provided
    if len(sys.argv) > 2:
        project_id = sys.argv[2]
        print(f"Using project ID: {project_id}")
    
    # Get output directory from command line if provided
    if len(sys.argv) > 3:
        output_base_dir = sys.argv[3]
        print(f"Using output directory: {output_base_dir}")

    try:
        # Fetch all data (fetch each entity type only once)
        push_events = get_push_events(project_id, since, until)
        commits = get_commits(project_id, since, until)
        # Only fetch all merge requests (contains opened, closed, merged)
        merge_events = get_merge_events(project_id)
        # Only fetch all issues (contains closed, service desk, bugs)
        issue_events = get_issue_events(project_id, since, until)
        milestones = get_milestones(project_id, since, until)

        milestones_in_month = []
        for milestone in milestones:
            created_at_str = milestone.get("created_at")
            if created_at_str:
                created_at = pd.to_datetime(created_at_str, utc=True).tz_localize(None)
                # Make since and until timezone-naive
                since_naive = since.replace(tzinfo=None)
                until_naive = until.replace(tzinfo=None)
                if since_naive <= created_at <= until_naive:
                    milestones_in_month.append(milestone)

        for milestone in milestones_in_month:
            print(f"Milestone Title: {milestone['title']}, Created At: {milestone['created_at']}")

        # Convert to DataFrame for better visualization
        push_df = pd.DataFrame(push_events) if isinstance(push_events, list) else pd.DataFrame()
        commits_df = pd.DataFrame(commits) if isinstance(commits, list) else pd.DataFrame()
        merge_df = pd.DataFrame(merge_events) if isinstance(merge_events, list) else pd.DataFrame()
        issue_df = pd.DataFrame(issue_events) if isinstance(issue_events, list) else pd.DataFrame()
        milestones_df = pd.DataFrame(milestones_in_month) if isinstance(milestones_in_month, list) else pd.DataFrame()
        
        # Function to filter dataframe by created_at
        def filter_by_date(df, since, until, date_column='created_at'):
            if df.empty or date_column not in df.columns:
                return df
            
            # Convert the date column to a timezone-aware UTC format
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce', utc=True)
            
            # Convert `since` and `until` to timezone-aware UTC
            since_utc = pd.to_datetime(since).tz_localize('UTC')
            until_utc = pd.to_datetime(until).tz_localize('UTC')
            
            # Filter the DataFrame based on the date column
            filtered_df = df[(df[date_column] >= since_utc) & (df[date_column] <= until_utc)]
            
            # Convert timezone-aware datetime to timezone-naive for Excel compatibility
            if date_column in filtered_df.columns:
                filtered_df = filtered_df.copy()
                filtered_df[date_column] = filtered_df[date_column].dt.tz_convert('UTC').dt.tz_localize(None)
            
            return filtered_df

        # Function to remove timezone info from all datetime columns for Excel compatibility
        def remove_timezone_info(df):
            if df.empty:
                return df
            df_copy = df.copy()
            for col in df_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    if hasattr(df_copy[col].dtype, 'tz') and df_copy[col].dtype.tz is not None:
                        df_copy[col] = df_copy[col].dt.tz_convert('UTC').dt.tz_localize(None)
                    # Convert to string for Excel
                    df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            return df_copy

        # Filter merge DataFrames (these don't have date filters in API, so filter manually)
        filtered_merge_df = filter_by_date(merge_df.copy(), since, until)
        
        # Filter issue events by updated_at if available
        filtered_issue_df = filter_by_date(issue_df.copy(), since, until, 'updated_at') if 'updated_at' in issue_df.columns else issue_df

        print(f"Push events: {len(push_df)}")
        print(f"Commits: {len(commits_df)}")
        print(f"Merge requests (all states): {len(filtered_merge_df)}")
        print(f"Issues (all types): {len(filtered_issue_df)}")
        print(f"Milestones: {len(milestones_df)}")

        # Use the unified Excel saving function
        merged_output_file, commits_output_file, output_dir = save_gitlab_data_to_excel(
            push_events, commits, merge_events, issue_events, milestones, since, until, output_base_dir
        )
        print(f"Events saved to Excel files: {merged_output_file} and {commits_output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")