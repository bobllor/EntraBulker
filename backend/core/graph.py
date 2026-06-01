from msal import PublicClientApplication
from msal.oauth2cli.oauth2 import BrowserInteractionTimeoutError
from logger import Log
from typing import Any, Callable
from support.types import Response
from core.types.graph import CreateUserJson, JsonHeaders, RequestErrorResponse
import requests
import support.utils as utils

GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"
GRAPH_CREATE_USER_URL: str = f"{GRAPH_BASE_URL}/users"
GRAPH_ME_URL: str = f"{GRAPH_BASE_URL}/me"

REQ_TIMEOUT: int = 20

def requests_handler(f: Callable[[Any], Response]) -> Response:
    '''Decorator used to wrap requests methods in a try-except and logs with
    errors if one occurs.

    The method must be a class with a logging instance self.log, and the method must return a Response.

    Any error exceptions will return the error `status`, the error `message`, and a None `content`.
    '''
    def wrapper(self, *args, **kwargs):
        try:
            res: Response = f(self, *args, **kwargs)

            return res
        except requests.exceptions.Timeout:
            self.log.exception(f"Request timeout")
            return utils.generate_response("error", message="Request timed out", content=None)
        except requests.exceptions.ConnectionError:
            self.log.exception(f"Connection failure")
            return utils.generate_response("error", message="Connection error while performing request", content=None)
        except Exception:
            self.log.exception(f"An unexpected error occurred during a request")
            return utils.generate_response("error", message="An unknown error occurred", content=None)
    
    return wrapper

class Graph:
    '''Class used for Microsoft Graph based operations.'''
    def __init__(self, client_id: str, tenant_id: str, *, log: Log = None):
        self._client_id: str = client_id
        self._tenant_id: str = tenant_id

        self.log: Log = log or Log()

        self._auth_url: str = f"https://login.microsoftonline.com/{self._tenant_id}"

        self.token: str = None
        # set in authenticate on succcessful token retrieval
        self.bearer: str = ""

        # set inside authenticate
        self.app: PublicClientApplication = None

        # least privilege scope that allows writing to entra, do not change!
        self._scopes: list[str] = ["User.ReadWrite.All"]

    @requests_handler 
    def is_authenticated(self) -> Response:
        '''Checks if the client is authenticated. It will return a Response with the
        status of the authentication in content.

        If the token is None, then it will return not authenticated. A request is sent
        to check if a token exists.

        The Response status will always be success, unless an exception occurs during
        the request itself in which case it will be an error.
        '''
        not_res: Response = utils.generate_response("success", message="Not authenticated", content=False)
        if self.token is None:
            return not_res

        res: Response = utils.generate_response("success", message="Authenticated", content=True)

        headers: JsonHeaders = {
            "authorization": self.bearer,
        }

        # due to it being a GET the timeout can afford to be less
        timeout: str = REQ_TIMEOUT // 2
        getres: requests.Response = requests.get(GRAPH_ME_URL, headers=headers, timeout=timeout) 
        json: dict[str, Any] = getres.json()

        if not getres.ok:
            err: RequestErrorResponse = self.get_error(json)
            self.log.info(f"Authentication status: {err} | Code: {err.code} | Message: {err.message}")

            return not_res

        return res

    def authenticate(self) -> Response:
        '''Authenticates the client and retrieves the token for use in requests.'''
        res: Response = utils.generate_response(message="Successfully authenticated")
        self.log.info("Starting authentication process for Graph API")

        app: PublicClientApplication = PublicClientApplication(
            self._client_id,
            authority=self._auth_url,
        )

        self.app = app

        if self.token is None:
            timeout_seconds: int = 180
            try:
                auth_res: dict[str, Any] = app.acquire_token_interactive(self._scopes, timeout=timeout_seconds)
                token_key: str = "access_token"
            except BrowserInteractionTimeoutError:
                self.log.info(f"Authentication timeout reached: User did not complete the flow in time")

                return utils.generate_response("error", message="Authentication timed out")
            
            if token_key in res:
                self.token = auth_res.get(token_key)
                self.bearer = f"Bearer {self.token}"
            else:
                errorStr: str = f"error={auth_res.get('error')};desc={auth_res.get('error_description')};id={auth_res.get('correlation_id')}"
                self.log.error(
                    f"Failed to authenticate Graph API | {errorStr}"
                )
                res = utils.generate_response("error", message="Failed to authenticate")

                return res
            
            self.log.info("Successfully authenticated")
            self.log.debug(f"Access token length: {len(self.token)}")
        else:
            self.log.info("Already authenticated")
            res["message"] = "Already authenticated"

        return res

    @requests_handler 
    def create_users(self, users: list[CreateUserJson]) -> Response:
        '''Sends a POST request and creates the users. Errors that occur will not interrupt other users
        given in the list but will be logged.

        Any error that will occur automatically will mark the Response as an error. 
        
        If all users  given failed to POST for whatever reason, then it will return an *error*. 
        If there are a handful of failed POST requests, then it will return a *warning*. 
        '''
        end_res: Response = utils.generate_response(message=f"Created users")
        headers: JsonHeaders = {
            "authorization": self.bearer,
            "content-type": "application/json"
        }

        created_users: list[str] = []
        failed_users: list[str] = []

        post_user_info = {
            "total users": len(users),
            "created users": {"users": created_users},
            "failed users": {"users": failed_users},
        }
        for user_json in users:
            post_res: requests.Response = requests.post(GRAPH_CREATE_USER_URL, json=user_json, headers=headers, timeout=REQ_TIMEOUT)
            data: dict[str, Any] = post_res.json()

            self.log.debug(f"POST response: {data}")

            if not post_res.ok:
                error: RequestErrorResponse = self.get_error(data)
                self.log.warning(f"Failed to create user {user_json['userPrincipalName']}: {error.message} | Code: {error.code}")
                failed_users.append(user_json["userPrincipalName"])
            else:
                self.log.info(f"Created user {user_json['userPrincipalName']}")
                created_users.append(user_json['userPrincipalName'])

        if len(failed_users) > 0:
            end_res["status"] = "warning"
            end_res["message"] = f"Failed to add {len(failed_users)}/{len(users)} user(s) with Graph API"
        if len(failed_users) == len(users):
            end_res["status"] = "error"
            end_res["message"] = f"Failed to add all given user(s) with Graph API"

        post_user_info["created users"]["Count"] = len(created_users)
        post_user_info["failed users"]["Count"] = len(failed_users)
        
        self.log.debug(f"POST users created: {post_user_info}")
        
        return end_res
    
    def get_error(self, d: dict[str, Any]) -> RequestErrorResponse:
        '''Parses a dictionary and creates a new RequestErrorResponse.
        
        Missing values will be an None if missing.
        '''
        code: str = utils.get_key(d, "code")
        err_msg: str = utils.get_key(d, "message")
        date: str = utils.get_key(d, "date")
        request_id: str = utils.get_key(d, "request-id")

        err = RequestErrorResponse(code, err_msg, date, request_id)
        
        return err