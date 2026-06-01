from typing import TypedDict, Literal
from dataclasses import dataclass

class PasswordProfileJson(TypedDict):
    forceChangePasswordNextSignIn: bool
    password: str

type UserType = Literal["member", "guest"]

class CreateUserJson(TypedDict):
    # The status of the account. Can be true or false.
    accountEnabled: bool

    # The name in displayed in the directory. This is the full name of the user.
    displayName: str

    # The mail alias of the user. This should be `user` of `user@domain.com`, as it is by default.
    mailNickname: str

    # The "email" of the user, or the principal name. For example, `user@domain.com`.
    userPrincipalName: str

    # The type of user, this is either Member or Guest. This will be a setting to enable
    # in the options. It will apply to every user being created.
    userType: UserType

    # The password profile of the user.
    passwordProfile: PasswordProfileJson

    # The first name of the user.
    givenName: str

    # The last name of the user.
    surname: str

@dataclass
class RequestErrorResponse:
    '''A class representing the error response of a Graph request.'''
    code: str = ""
    message: str = ""
    date: str = ""
    request_id: str = ""

JsonHeaders = TypedDict("JsonHeaders",
    {
        "authorization": str,
        "content-type": str,
    }
)