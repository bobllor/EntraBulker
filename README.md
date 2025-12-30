# EntraBulker

*EntraBulker* is a customizable application that generates CSV files for bulking Entra ID identities 
without the need for API access.

## Install

The application is ***only supported on Windows.***

Installation can be done through the [releases page](https://github.com/bobllor/EntraBulker/releases/) 
via the binary or ZIP file.

The [binary](https://github.com/bobllor/EntraBulker/releases/download/v1.0.0/entrabulker-installer.exe) is a standalone installer
that installs the program onto your device.
- The default installation path is `$HOME\AppData\Programs\EntraBulker`, the path can be changed as needed.
- It is the recommended way as it creates a shortcut automatically and can be uninstalled via *Control Panel*.

The ZIP file contains a folder `entrabulker` that holds the required files in the folder.
The folder structure is like so:
- `apps`
    - `madist`
    - `EntraBulker.exe`: Main application
- `udist`
- `EntraUpdater.exe`

The files can be extracted to a given location and the application can be launched via `EntraBulker.exe` located in the `apps` folder.
It is *recommended* to make a shortcut of `EntraBulker.exe` in order to use it outside of the folder.

## Usage

The application has two ways to generate CSV files:
1. File uploading
2. Manual entries

Both ways will have a submit button. Upon submission, the files will be generated to an output folder. 
By default, this is your *home* folder, which can be changed in the *General settings tab*.

### Settings

The settings allow customization on how the application will function. There are five tabs:
1. [General](./docs/settings/general.md)
2. [Headers](./docs/settings/headers.md)
3. [Organization](./docs/settings/organization.md)
4. [Password](./docs/settings/password.md)
5. [Text Template](./docs/settings/text_template.md)

### File Uploading

The application only supports CSV (`.csv`) and Excel (`.xlsx`) files.

The files are expected to have the following columns (or any related columns). These columns can be mapped
to any value as needed in the *Headers settings tab*. The following columns are expected:
1. Full Name*
2. Organization
3. First Name*
4. Last Name*

\*The names are dependent on the option `First/Last Name Headers` in the *General settings tab*, which is off by default.
The program **looks for a Full name column** first, but if First and Last name columns are required, then enabling the 
option will change the program to look for both columns instead of the single column.

It is important to note that the column mappings can be changed inside the ***Headers settings tab*** if the default values
do not match your columns. More information can be read [here](./docs/settings/headers.md).