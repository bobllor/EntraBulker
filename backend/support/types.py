from typing import TypedDict, Literal

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

class HeaderMap(TypedDict):
    opco: str
    name: str

class OpcoMap(TypedDict):
    default: str

# for subsititions, the text must contain enclosed brackets [] around
# the following three keys (CASE-SENSITIVE): NAME, PASSWORD, USERNAME
class TemplateMap(TypedDict):
    enabled: bool
    text: str
    words_to_replace: str

class Formatting(TypedDict):
    format_type: Literal["period", "no space"]
    format_case: Literal["title", "upper", "lower"]
    format_style: Literal["first last", "f last", "first l"]

class Password(TypedDict):
    length: int
    use_uppercase: bool
    use_punctuations: bool

# NOTE: this will need to be updated in types.ts as well.
class APISettings(TypedDict):
    output_dir: str
    flatten_csv: bool
    template: TemplateMap
    format: Formatting
    password: Password

# NOTE: can contain other keys if used.
class Response(TypedDict):
    status: Literal["success", "error"]
    message: str