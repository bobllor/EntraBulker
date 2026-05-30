from typing import TypedDict

class PasswordProfileJson(TypedDict):
    forceChangePasswordNextSignIn: bool
    password: str

class CreateUserJson(TypedDict):
    accountEnabled: str
    displayName: str
    # i think this is the user of user@domain.com?
    mailNickname: str
    passwordProfile: PasswordProfileJson
    # e.g. user@domain.com
    userPrincipalName: str

JsonHeaders = TypedDict("JsonHeaders",
    {
        "authorization": str,
        "content-type": str,
    }
)