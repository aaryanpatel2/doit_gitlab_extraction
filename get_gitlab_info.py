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
        # Fetch all data
        push_events = get_push_events(project_id, since, until)
        commits = get_commits(project_id, since, until)
        merge_events = get_merge_events(project_id)
        merge_events_opened = get_merge_events_opened(project_id)
        merge_events_closed = get_merge_events_closed(project_id)
        merge_events_merged = get_merge_events_merged(project_id)
        issue_events = get_issue_events(project_id, since, until)
        milestones = get_milestones(project_id, since, until)
        service_desk_issues = get_service_desk_issues(project_id, since, until)
        closed_issues = get_closed_issues(project_id, since, until)

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
        merge_df_opened = pd.DataFrame(merge_events_opened) if isinstance(merge_events_opened, list) else pd.DataFrame()
        merge_df_closed = pd.DataFrame(merge_events_closed) if isinstance(merge_events_closed, list) else pd.DataFrame()
        merge_df_merged = pd.DataFrame(merge_events_merged) if isinstance(merge_events_merged, list) else pd.DataFrame()
        issue_df = pd.DataFrame(issue_events) if isinstance(issue_events, list) else pd.DataFrame()
        milestones_df = pd.DataFrame(milestones_in_month) if isinstance(milestones_in_month, list) else pd.DataFrame()
        service_desk_df = pd.DataFrame(service_desk_issues) if isinstance(service_desk_issues, list) else pd.DataFrame()
        closed_issues_df = pd.DataFrame(closed_issues) if isinstance(closed_issues, list) else pd.DataFrame()
        
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
        filtered_merge_df_opened = filter_by_date(merge_df_opened.copy(), since, until)
        filtered_merge_df_closed = filter_by_date(merge_df_closed.copy(), since, until)
        filtered_merge_df_merged = filter_by_date(merge_df_merged.copy(), since, until)
        
        # Filter issue events by updated_at if available
        filtered_issue_df = filter_by_date(issue_df.copy(), since, until, 'updated_at') if 'updated_at' in issue_df.columns else issue_df

        print(f"Push events: {len(push_df)}")
        print(f"Commits: {len(commits_df)}")
        print(f"Filtered merge events: {len(filtered_merge_df)}")
        print(f"Filtered opened merge events: {len(filtered_merge_df_opened)}")
        print(f"Filtered closed merge events: {len(filtered_merge_df_closed)}")
        print(f"Filtered merged merge events: {len(filtered_merge_df_merged)}")
        print(f"Issue events: {len(filtered_issue_df)}")
        print(f"Service Desk issues: {len(service_desk_df)}")
        print(f"Milestones: {len(milestones_df)}")

        # Remove timezone info from all DataFrames before saving to Excel
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

        # Create filename prefix with year-month
        year_month_prefix = since.strftime('%Y-%m')

        # Create output directory if it doesn't exist
        output_dir = os.path.join(output_base_dir, year_month_prefix)
        os.makedirs(output_dir, exist_ok=True)

        bug_issues = get_bug_issues(project_id, since, until)
        bug_issues_df = pd.DataFrame(bug_issues) if isinstance(bug_issues, list) else pd.DataFrame()
        bug_issues_df_clean = remove_timezone_info(bug_issues_df)

        def merge_on_project_id(left, right):
            # Only keep columns in right that are not in left, except for 'project_id'
            right_unique = right[[col for col in right.columns if col not in left.columns or col == 'project_id']]
            return pd.merge(left, right_unique, on='project_id', how='outer')

        # Filter out empty DataFrames and those without 'project_id'
        dfs_to_merge = [
            df for df in [
                push_df_clean,
                filtered_merge_df_clean,
                filtered_merge_df_opened_clean,
                filtered_merge_df_closed_clean,
                filtered_merge_df_merged_clean,
                filtered_issue_df_clean,
                milestones_df_clean,
                service_desk_df_clean,
                closed_issues_df_clean,
                bug_issues_df_clean
            ] if not df.empty and 'project_id' in df.columns
        ]

        if dfs_to_merge:
            merged_df = reduce(merge_on_project_id, dfs_to_merge)
        else:
            merged_df = pd.DataFrame()

        # Write merged data (all except commits) to one file
        merged_output_file = os.path.join(output_dir, f"{year_month_prefix}_all_gitlab_info.xlsx")
        merged_df.to_excel(merged_output_file, index=False)

        # Write commits to a separate file
        commits_output_file = os.path.join(output_dir, f"{year_month_prefix}_commits.xlsx")
        commits_df_clean.to_excel(commits_output_file, index=False)

        print(f"Events saved to Excel files: {merged_output_file} and {commits_output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")