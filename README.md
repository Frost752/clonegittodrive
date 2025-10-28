# GitRepoToGoogleDriveBackup

## Overview

This repository contains a Python script that backs up a specified Git repository to a designated folder on Google Drive. The script uses the Google Drive API to authenticate, create folders, and upload files, ensuring that the backup process is seamless and automated.

## Features

    Automated backup of Git repositories to Google Drive.

    Support for specific commit hashes or tags for backup.

    Creation of a structured folder hierarchy on Google Drive, mirroring the repository's directory structure.

    Authentication with Google Drive using OAuth 2.0.

    Generation of a changelog file for the backup, detailing the commits included.

## Requirements

    Python 3.6 or later.

    Google Drive API credentials (JSON file).

    `gitpython` library for Git operations.

    `google-auth`, `google-auth-oauthlib`, and `google-api-python-client` libraries for Google Drive API interactions.

## Installation

First, ensure you have Python 3.6 or later installed. Then, install the required Python packages.

```bash
pip install gitpython google-auth google-auth-oauthlib google-api-python-client
```

## Usage

### 1. Set Up Google Drive API Credentials

Before you can interact with Google Drive through the API, you need to set up the credentials and configure the necessary permissions. Follow these steps:

#### Step 1: Create a Project in Google Cloud Console

1. **Go to the Google Cloud Console**:
   - Open the [Google Cloud Console](https://console.cloud.google.com/).
   
2. **Create a New Project**:
   - In the Cloud Console, click on the project dropdown on the top-left, then click **New Project**.
   - Enter a name for your project and select your billing account (if applicable).
   - Click **Create**.

#### Step 2: Enable the Google Drive API

1. **Navigate to the API Library**:
   - In the Google Cloud Console, open the **Navigation menu** (top-left) > **APIs & Services** > **Library**.

2. **Enable Google Drive API**:
   - In the search bar, type `Google Drive API`.
   - Click on it and then click **Enable**.

#### Step 3: Create OAuth 2.0 Credentials

1. **Go to the Credentials Page**:
   - In the Google Cloud Console, open **APIs & Services** > **Credentials**.

2. **Create Credentials**:
   - Click on the **Create Credentials** button and select **OAuth client ID**.

3. **Configure OAuth Consent Screen**:
   - If you haven’t configured the consent screen yet, you'll need to do so. Fill in the required fields (app name, user support email, etc.).
   - Under **Scopes**, you can leave the default settings unless you need to request specific permissions.
   - Click **Save and Continue**.

4. **Choose Application Type**:
   - Select **Desktop App** as the application type.
   - Provide a name for your OAuth 2.0 client (e.g., "Drive API Client").
   - Click **Create**.

5. **Download `credentials.json`**:
   - After creating the credentials, you’ll see a dialog with your newly created credentials.
   - Click the **Download** button to download the `credentials.json` file. This file contains the client ID and secret needed to authenticate your app.

### 2. Run the Backup Script

Use the command line to run the backup script with the appropriate arguments.

```bash
python backup_script.py --repo /path/to/repo --folder YOUR_DRIVE_FOLDER_ID [--commit COMMIT_HASH_OR_TAG]
```

    --repo or -r: Path to the Git repository (default: current directory).
    --folder or -f: Google Drive root folder ID for backups (required).
    --commit or -c: Specific commit hash or tag to back up (default: HEAD).

## Development

Clone the repo with:

```bash
git clone https://github.com/Frost752/clonegittodrive.git
cd clonegittodrive
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any improvements or new features to add.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.