# General Settings

The General settings has options that modifies the output file and the option to enable first/last name columns.

<img src="./assets/general-settings.png" alt="General settings" width="600" >

## Flatten CSV

By default, each file uploaded will have its own output. If a single file is preferred, this option *merges all
uploaded files into a single output*.

If *Generate Text is enabled*, then all generated files will be outputted to the same folder.

## Generate Text

Generate Text enables text file generations for each user in the row. This allows for *sharing login information*
with a template. This does require a *non-empty text submission* that can be set in the [Text Template settings tab](./text_template.md).

This will create a new folder in the output path called `templates`, and will contain a subfolder that holds the files for
each uploaded file with a unique hash attached to the name.
- If `Flatten CSV` is enabled, then all files will instead be outputted into the same subfolder.

## First/Last Name Headers

This option changes the way the data is parsed by the program. 

By default, parsing looks for *a single full name column* for the name of the user. In case data files 
do not use a full name column but two columns for first/last, this option enables the support of the double column.

This changes the program to use the First/Last Name columns as *defined in the Headers tab*.

<img src="./assets/headers-first-last.png" alt="First/Last column mapping" width="600" >

### Example

The example will use the default header values.

Input file:

| First name | Last name | Operating company |
| --- | --- | --- |
| John | Doe | Company one |
| Jane | Doe | Company one |
| James | Smith | Company two |

Output file (version row excluded):

| Name [displayName] Required | User name [userPrincipalName] Required | Initial password [passwordProfile] Required | Block sign in (Yes/No) [accountEnabled] Required | First name [givenName] | Last name [surname] |
| --- | --- | --- | --- | --- | --- |
| John Doe | John.Doe@company.one.org | F7nC?o/i_"N(WvHE | No | John | Doe |
| Jane Doe | Jane.Doe@company.one.org | FGpE&=mH`{kg6#X, | No | Jane | Doe |
| James Smith | James.Smith@two.company.com | "_.2yCcr"U!eX\|"y | No | James | Smith |

The output is the same as if it were using the Full name column only.

## Name Formatting

The application generates usernames as the format `First.Last@domain.com` by default, using the first and last names
of the user. This can be modified with the name formatting options.

There are three dropdown menu options which is used to format the username based off of their names:
1. [**Format type**](#format-type): The type of format used on the username
2. [**Format style**](#format-style): The username will appear based off of the name
3. [**Format case**](#format-case): The casing of the username based off of the name

### Format Type

Consists of two options:
1. **Period**: Adds a period for the username: `John.Doe@domain.com` (default)
2. **No space**: Does not add a space for the username: `JohnDoe@domain.com`

### Format Style

Consists of three options:
1. **First Last**: Takes the full first and last name: `John.Doe@domain.com` (default)
2. **F Last**: Takes the first letter of the first name and the full last name: `J.Doe@domain.com`
3. **First L**: Takes the full first and first letter of the last name: `John.D@domain.com`

### Format Case

Consists of three options:
1. **Uppercase**: Username portion is entirely uppercase: `JOHN.DOE@domain.com`
2. **Lowercase**: Username portion is entirely lowercase: `john.doe@domain.com`
3. **Title case**: Username portion is in title case: `John.Doe@domain.com` (default)

This only effects the display in the system, usernames are case insensitive and does not effect
how it will be used.