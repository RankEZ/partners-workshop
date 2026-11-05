In RankEZ, writing or pushing a password to a file is handled through two primary mechanisms depending on the operational scenario: **Account Usage Management (CPM For File)** for pushing rotated passwords into remote configuration files, and the **`aimexec` tool (using the `!file` tag)** in Application Identity Management (AIM) for local application execution.

---

### 1. Account Usage Management (`CPM For File`)
When an application relies on a password stored in a configuration file on a target server, RankEZ uses **Account Usage Management** to push updated passwords directly into that file whenever CPM rotates or changes the credential.

**Configuration Steps:**
1. Navigate to **Account >> Account Usage** in the console and click **[+ Usage]**.
2. **Define Objects**:
   - **Reference Devices & Account**: Select the managed device and account whose password is referenced in the configuration file.
   - **Target Devices & Handle Account**: Select the target machine and the administrative connection account that executes the file update.
3. **Select Usage Type**:
   - Choose a file usage type such as **Windows/Linux Text File (Txt)**, **INI**, or **XML**.
4. **Configure File Parameters**:
   - **Target File Path**: Specify the exact path to the target configuration file.
   - **File Backup**: Option to automatically back up the target file before pushing updates.
   - **Regular Expression Pattern**: Define the regex pattern used to locate and overwrite the password string inside the target file.
5. **Execution**:
   - **Automated Push**: CPM automatically pushes the new password into the configuration file whenever the referenced account password is changed or rotated.
   - **Manual Push**: Can be triggered on demand by clicking the **Push** button next to the usage record on the Account Usage page.

