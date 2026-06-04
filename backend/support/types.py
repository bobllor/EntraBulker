from typing import TypedDict, Literal
from core.types.graph import UserType

class GenerateCSVProps(TypedDict):
    fileName: str
    b64: str

class ManualCSVProps(TypedDict):
    name: str
    opco: str
    id: str

class AzureHeaders(TypedDict):
    name: str
    username: str
    password: str
    block_sign_in: str
    first_name: str
    last_name: str

class OpcoMap(TypedDict):
    default: str

class Metadata(TypedDict):
    version: str
    version_url: str
    releases_url: str

class FileNames(TypedDict):
    '''The main files of the application in the project root.'''
    app_exe: str
    app_dist: str
    updater_exe: str 
    updater_dist: str
    project_folder: str
    apps_folder: str

# for subsititions, the text must contain enclosed brackets [] around
# the following three keys (CASE-SENSITIVE): NAME, PASSWORD, USERNAME
class TemplateMap(TypedDict):
    enabled: bool
    text: str

class Formatting(TypedDict):
    format_type: Literal["period", "no space"]
    format_case: Literal["title", "upper", "lower"]
    format_style: Literal["first last", "f last", "first l"]

class Password(TypedDict):
    length: int
    use_uppercase: bool
    use_punctuations: bool
    use_numbers: bool

# NOTE: this will need to be updated in types.ts as well.
class APISettings(TypedDict):
    output_dir: str
    flatten_csv: bool
    two_name_column_support: bool
    template: TemplateMap
    format: Formatting
    password: Password

# NOTE: can contain other keys if used.
class Response(TypedDict):
    status: Literal["success", "error", "warning"]
    message: str

class UserData(TypedDict):
    usernames: list[str]
    full_names: list[str]
    passwords: list[str]

# by the way, fuck python and their imports. did i say this already?
class GraphMap(TypedDict):
    client_id: str
    tenant_id: str

    # Enables Graph requests during the Azure CSV generation. By default
    # this is false. It also requires authentication, which will always be
    # if this option is true.
    enable_graph: bool

    # Creates the users as `Member` or as `Guest`. This will cause all users
    # to be created of one type. By default, all users are created as Member in 
    # Entra ID.
    user_type: UserType

    # If true, always attempt to authenticate on boot. This only applies to the
    # token cache and will not attempt an interactive browser token attempt.
    reauthenticate_on_boot: bool

    # A CSV-style string containing domains that will always be of the type `Member`.
    # This only applies if the `user_type` is set to `Guest`.
    #
    # For example, if the CSV value is `@example.com,another.example.com`, then the
    # then all domains that do not match these two domains will be converted to `Guest`.
    member_type_domain_csv: str

class HeaderMap(TypedDict):
    opco: str
    name: str
    first_name: str
    last_name: str