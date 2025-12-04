import os
import sys
import argparse
from git import Repo, GitCommandError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === CONFIG ===
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# === MAIN FUNCTION ===
def main():
    parser = argparse.ArgumentParser(description="Backup a Git repo to Google Drive.")
    parser.add_argument("--repo", "-r", default=os.getcwd(), help="Path to the Git repository (default: current directory).")
    parser.add_argument("--folder", "-f", required=True, help="Google Drive root folder ID for backups.")
    parser.add_argument("--commit", "-c", help="Specific commit hash or tag to back up (default: HEAD).")
    args = parser.parse_args()

    repo_path = args.repo
    root_drive_folder_id = args.folder
    commit_ref = args.commit or "HEAD"  # Default to HEAD if no commit is provided

    print(f"Starting Google Drive repo backup for '{repo_path}' with commit '{commit_ref}'...")
    backup_repo(repo_path, root_drive_folder_id, commit_ref)
    print("Program finished.")

# === AUTHENTICATION ===
def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    print("Authenticated with Google Drive.")
    return creds

# === DRIVE HELPERS ===
def create_folder(service, name, parent_id=None):
    folder_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        folder_metadata["parents"] = [parent_id]
    folder = service.files().create(
        body=folder_metadata,
        fields="id, name, parents",
        supportsAllDrives=True
    ).execute()
    print(f"Created folder '{name}' with ID {folder['id']}")
    return folder["id"]

def find_folder(service, name, parent_id=None):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None

def upload_file(service, filepath, parent_id):
    filename = os.path.basename(filepath)
    media = MediaFileUpload(filepath, resumable=True)
    file_metadata = {"name": filename, "parents": [parent_id]}
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name",
        supportsAllDrives=True,
    ).execute()
    print(f"Uploaded '{filename}' (ID: {uploaded_file['id']})")
    return uploaded_file["id"]

def get_or_create_drive_path(service, parent_id, relative_path):
    if not relative_path or relative_path == ".":
        return parent_id
    parts = relative_path.replace("\\", "/").split("/")
    current_parent = parent_id
    for part in parts:
        folder_id = find_folder(service, part, parent_id=current_parent)
        if not folder_id:
            folder_id = create_folder(service, part, parent_id=current_parent)
        current_parent = folder_id
    return current_parent

# === BACKUP REPO ===
def backup_repo(repo_path, root_drive_folder_id, commit_ref):
    if not os.path.exists(repo_path):
        print(f"Repository path '{repo_path}' does not exist.")
        return

    creds = authenticate()
    service = build("drive", "v3", credentials=creds)
    repo = Repo(repo_path)

    try:
        # Try to fetch the commit by the hash or tag provided
        commit = repo.commit(commit_ref)  # Use the provided commit or tag
    except ValueError:
        print(f"Invalid commit or tag reference: {commit_ref}")
        return
    except GitCommandError:
        print(f"Failed to retrieve commit with reference: {commit_ref}")
        return

    # If a tag is found for the commit, we can proceed, otherwise use commit hash
    tags = [t for t in repo.tags if t.commit == commit]
    tag_name = tags[0].name if tags else commit.hexsha
    repo_name = os.path.basename(os.path.abspath(repo_path))
    print(f"Backing up repo '{repo_name}', commit/tag '{tag_name}'")

    repo_folder_id = find_folder(service, repo_name, parent_id=root_drive_folder_id)
    if not repo_folder_id:
        repo_folder_id = create_folder(service, repo_name, parent_id=root_drive_folder_id)

    tag_folder_id = find_folder(service, tag_name, parent_id=repo_folder_id)
    if tag_folder_id:
        print(f"Tag/commit '{tag_name}' already backed up — skipping.")
        return
    tag_folder_id = create_folder(service, tag_name, parent_id=repo_folder_id)

    create_changelog(repo, tag_name, tag_folder_id, service, commit)

    for root, dirs, files in os.walk(repo_path):
        # Skip .git
        if ".git" in dirs:
            dirs.remove(".git")

        filtered_dirs = []
        for d in dirs:
            path = os.path.join(root, d)
            try:
                repo.git.check_ignore(path)
            except GitCommandError as e:
                if e.status == 1:
                    filtered_dirs.append(d)
                elif e.status != 0:
                    raise
        dirs[:] = filtered_dirs

        rel_root = os.path.relpath(root, repo_path)
        target_folder_id = get_or_create_drive_path(service, tag_folder_id, rel_root)

        for file in files:
            file_path = os.path.join(root, file)
            try:
                repo.git.check_ignore(file_path)
                continue  # ignored
            except GitCommandError as e:
                if e.status != 1:
                    raise
            upload_file(service, file_path, target_folder_id)

    print(f"Backup of '{repo_name}' (commit/tag: {tag_name}) completed!")

def create_changelog(repo, tag_name, target_folder_id, service, commit):
    # Fetch commits between the previous tag (if any) and the specified commit
    previous_tag = None
    sorted_tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    
    for i, t in enumerate(sorted_tags):
        if t.name == tag_name and i > 0:
            previous_tag = sorted_tags[i - 1].name
            break

    if previous_tag:
        commits = list(repo.iter_commits(f'{previous_tag}..{tag_name}'))
    else:
        commits = list(repo.iter_commits(f'{tag_name}'))
    
    commits.reverse()
    
    changelog_lines = [f"Tag/Commit: {tag_name}", f"Commit message: {commit.message.strip()}", "", "Commits included:"]
    for c in commits:
        changelog_lines.append(f"- {c.hexsha[:7]}: {c.message.strip()}")
    
    changelog_path = os.path.join(os.getcwd(), "CHANGELOG.txt")
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write("\n".join(changelog_lines))
    
    upload_file(service, changelog_path, target_folder_id)
    # os.remove(changelog_path)

if __name__ == "__main__":
    main()
