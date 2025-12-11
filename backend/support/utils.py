from core.names import NameFormatter, NoSpace, Period
from typing import Literal, Any, Callable
from support.types import Response
from pathlib import Path
import string, re, uuid, subprocess

def format_name(name: str, *, keep_full: bool = False) -> str:
    '''Formats and validates a name, by default the First and Last name only.
    
    Parameters
    ----------
        keep_full: bool, default False
            Boolean used to keep the full name instead of keeping only the First and Last.
    '''
    special_chars: set[str] = set(string.punctuation)
    
    chars: list[str] = []
    for c in name:
        if c not in special_chars and not c.isdigit():
            chars.append(c)
        
        if c == '-':
            chars.append('-')

    name: str = ''.join(chars)
    name_list: list[str] = name.split()

    unwanted_words: set[str] = {'jr', 'sr', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'the', 'of'}

    new_name: list[str] = []

    for name in name_list:
        name = name.lower().strip()
        
        is_valid: bool = re.match('^([A-Za-z-]*)$', name) != None
        has_bad_words: bool = name in unwanted_words

        if is_valid and not has_bad_words and len(name) > 1:
            new_name.append(name.title())

    if len(new_name) < 1:
        return "Invalid Name"

    f_name: str = new_name[0]
    if keep_full:
        f_name = " ".join(new_name[0:len(new_name) - 1])
    l_name: str = new_name[-1]

    # if the full name is 20 characters long, then only use the first letter of the first name.
    # i don't think this is necessary, i am unsure of the limit for azure. ServiceNow had this however.
    # TODO: needs testing on azure.
    '''if len(f'{f_name} {l_name}') > 20:
        return f'{f_name[0]} {l_name}'''

    return f'{f_name} {l_name}'

def check_duplicate_names(names: list[str]) -> list[str]:
    '''Checks a list of names for duplicates, if duplicates are found then a number 
    is appended to the name.

    The same list will be returned with the modification if it occurred.
    '''
    seen_names: dict[str, int] = {}
    new_names: list[str] = []

    for name in names:
        if name not in seen_names:
            seen_names[name] = 0
        else:
            seen_names[name] += 1
            name = name + str(seen_names[name])

        new_names.append(name)
    
    return new_names

def generate_response(status: Literal['error', 'success'] = 'success', **kwargs) -> dict[str, Any]:
    '''Generate a response dictionary.

    Common keys: status, message, content
    
    Parameters
    ----------
        status: str, default "success"
            The status of the response. It can only be two string values, "success" or "error".

        kwargs: dict[str, Any]
            Any keyword argument, this gets added into the response.
    '''
    res: dict[str, Any] = {"status": status}

    for key, value in kwargs.items():
        res[key] = value

    return res

def generate_usernames(
    names: list[str],
    opcos: list[str],
    opco_map: dict[str, str],
    *, 
    format_type: Literal["period", "no space"] = "period",
    format_style: Literal["first last", "f last", "first l"] = "first last",
    format_case: Literal["title", "lower", "upper"] = "title") -> list[str]:
    '''Generates a list of formatted usernames for Azure. Only the first and last name are
    taken. If dashes exist then it will be removed.
    
    Parameters
    ----------
        names: str
            A list of names for the account to be formatted.
        
        opcos: str, default None
            A list of operating companies for each user, it determines the domain used. If an operating company
            does not exist in the map, the default value will be used.

        opco_map: dict[str, str]
            A dictionary used to get the domain based on the operating company.

        format_type: Literal["period", "no space"], default "period"
            The username formatting type, it replaces spaces between the names with a specific character.
            By default it is "period", the specific character being a period (`"."`).

        format_style: Literal["first last", "f last", "first l"], default "first last"
            The username formatting style, this is the final output of the username. For example, the
            "f last" option results in "J.Doe". By default it is "first last".
        
        format_case: Literal["title", "lower", "upper"], default "title"
            Determines the case style of the username. By default it is title case: "first.last" ->
            "First.Last".
    '''
    format_dict: dict[str, NameFormatter] = {
        "period": Period,
        "no space": NoSpace
    }
    formatter: NameFormatter = format_dict[format_type](format_case)
    style_dict: dict[str, Callable[[str], str]] = {
        "first last": formatter.replace,
        "f last": formatter.f_last,
        "first l": formatter.first_l,
    }

    default_opco: str = opco_map.get('default', "MISSING_DEFAULT.com")
    usernames: list[str] = []

    for i, name in enumerate(names):
        name = format_hyphen_name(name.strip())
        username: str = style_dict[format_style](name)

        usernames.append(f'{username}@{opco_map.get(opcos[i], default_opco)}')

    return usernames    

def generate_username(
    name: str,
    opco: str,
    opco_map: dict[str, str],
    *, 
    format_type: Literal["period", "no space"] = "period",
    format_style: Literal["first last", "f last", "first l"] = "first last",
    format_case: Literal["title", "lower", "upper"] = "title") -> list[str]:
    '''Generates a list of formatted usernames for Azure.
    
    Parameters
    ----------
        name: str
            A name for the account to be formatted.
        
        opcos: str, default None
            An operating company for the user, it determines the domain used. If an operating company
            does not exist in the map, the default value will be used.

        opco_map: dict[str, str]
            A dictionary used to get the domain based on the operating company.

        format_type: Literal["period", "no space"], default "period"
            The username formatting type, it replaces spaces between the names with a specific character.
            By default it is "period", the specific character being a period (`"."`).

        format_style: Literal["first last", "f last", "first l"], default "first last"
            The username formatting style, this is the final output of the username. For example, the
            "f last" option results in "J.Doe". By default it is "first last".
        
        format_case: Literal["title", "lower", "upper"], default "title"
            Determines the case style of the username. By default it is title case: "first.last" ->
            "First.Last".
    '''
    format_dict: dict[str, NameFormatter] = {
        "period": Period,
        "no space": NoSpace
    }
    formatter: NameFormatter = format_dict[format_type](format_case)
    style_dict: dict[str, Callable[[str], str]] = {
        "first last": formatter.replace,
        "f last": formatter.f_last,
        "first l": formatter.first_l,
    }

    default_opco: str = opco_map.get('default', "MISSING_DEFAULT.com")
    name = format_hyphen_name(name.strip())
    username: str = style_dict[format_style](name)

    return f'{username}@{opco_map.get(opco, default_opco)}'

def format_hyphen_name(name: str) -> str:
    '''Formats the name of the hyphen to extract the First and Last names only.'''
    if "-" in name:
        names: list[str] = name.split()
        temp_name: list[str] = []

        for i, n in enumerate(names):
            # ignores any hyphens that arent the first or last names.
            if "-" in n and (i == 0 or i == len(names) - 1): 
                temp_n: list[str] = n.split("-")

                temp_name.append(temp_n[0 if len(temp_name) == 0 else -1])
                continue
            
            # this handles if we have hyphens in the middle of names
            if i == 0 or i == len(names) - 1: 
                temp_name.append(n)

        name = " ".join(temp_name)
    
    return name

def get_date(date_format: str = '%Y-%m-%dT%H%M%S') -> str:
    '''Get the date, by default it returns the format YY-MM-DD-HHMMSS'''
    from datetime import datetime

    date: str = datetime.today().strftime(date_format)

    return date

def generate_password(max_length: int = 16, *, 
    use_punctuations: bool = False, 
    use_uppercase_letters: bool = False,
    use_numbers: bool = False) -> str:
    '''Random password generation. The password will always have a minimum of one upper, one lower, and one special character.
    
    Parameters
    ----------
        max_length: int, default `16`
            The max length of the password. By default it is 16 characters long.
        
        use_punctuations: bool, default `False`
            If true, then punctuations are used in the password.

        use_uppercase_letters: bool, default `False`
            If true, then uppercase letters are used in the password.
        
        use_numbers: bool, default `False`
            If true, then numbers are used in the password.
    '''
    # FIXME: add a profanity checker?
    import random, string

    pw: list[str] = []

    upper: string = string.ascii_uppercase
    lower: string = string.ascii_lowercase
    numbers: string = "0123456789"

    # TODO: why is this not allowed? this needs to be tested.
    # i'd rather disallow ' " \ | ; / < >
    # ' - % $ are not allowed
    punctuations: string = ''.join([c for c in string.punctuation if c not in '-%\''])

    valid_chars: string = lower

    if use_punctuations:
        valid_chars += punctuations
    if use_uppercase_letters:
        valid_chars += upper
    if use_numbers:
        valid_chars += numbers

    # need at least one upper, lower, and special
    for seq in [upper, lower, punctuations]:
        pw.append(random.choice(seq))

    new_length: int = max_length - 3

    for _ in range(new_length):
        pw.append(random.choice(valid_chars))
    
    random.shuffle(pw)
    
    return "".join(pw)

def generate_text(*, 
    text: str, 
    username: str = '', 
    password: str = '',
    name: str = '') -> Response:
    '''Replaces strings in a text template.

    There are key words that can be replaced: USERNAME, PASSWORD, and NAME.

    In order to replace them, the exact variable ***must be enclosed by brackets***.

    The key words are ***case sensitive***, the function expects all of it to be uppercase only.

    Example:
    ```python
    password, name = password1234, John Doe
    text = "Hello [NAME], your password is [PASSWORD] and your username is [USERNAME]."
    print(text) # "Hello John Doe, your password is password1234 and your username is [USERNAME]."
    ```
    
    This will replace **all** occurrences of the brackets.
    If no values are passed in the variables, then no replacements will occur to that key word in the text.

    Parameters
    ----------
        text: str
            The text used that is being replaced, it has a max length of 500. The words being replaced
            **must be surrounded by brackets**, e.g. [NAME].
        
        username: str, default ''
            The username of the client.
        
        password: str, default ''
            The password of the client. This is stored as **plain text**, and it is best practice to enable
            “User must change password at next logon” on Azure.
        
        name: str, default ''
            Name of the client.
    '''
    text = text.strip()
    max_chars: int = 1250

    # this is going to get checked on the front end but it won't hurt to have this just in case.
    if len(text) > max_chars:
        return generate_response(
            status='error', 
            message=f'Cannot have a text of over {max_chars} characters.',
            content="",    
        )

    key_words: list[str] = ['USERNAME', 'PASSWORD', 'NAME']
    data: list[str] = [username, password, name]

    for i in range(len(key_words)):
        replace_word: str = data[i].title() if key_words[i] == 'NAME' else data[i]
        text = text.replace(f'[{key_words[i]}]', replace_word)
    
    return generate_response(status='success', 
        message='Successfully generated the text in the output folder.',
        content=text)

def format_value(value: Any) -> Any:
    '''Formats a value for logging purposes. 
    
    This is **not to be used** for final data, rather it is only 
    used to format data for the log.
    '''
    if isinstance(value, str) and len(value) > 200:
        value = value[0:200] + "..."

    return value

def get_id(divisor: int = 4) -> str:
    '''Generates a random uuid4.'''
    uid: str = uuid.uuid4().hex

    if divisor == 0:
        return uid

    return uid[:int(len(uid) / divisor)]

def unlink_path(path: Path) -> None:
    '''Method to remove a given Path. If the path is a directory, then
    recursively remove all of its contents and itself.'''
    if path.is_dir():
        for child in path.iterdir():
            if not child.is_dir():
                child.unlink()
            else:
                unlink_path(child)
        
        path.rmdir()
    else:
        path.unlink()

def run_cmd(cmd: list[str]) -> None:
    '''Executes a command through subprocess.'''
    blacklisted_cmd: set[str] = {
        "rm", "rmdir", "ri", "del",
        "rd", "erase", "remove-item"
    }

    for string in cmd:
        if string.lower() in blacklisted_cmd:
            return "", f"Error: blacklisted command {string} used as argument"

    process: subprocess.CompletedProcess[bytes] = subprocess.run(cmd, capture_output=True)

    out: str = process.stdout.decode()
    err: str = process.stderr.decode()

    return out, err