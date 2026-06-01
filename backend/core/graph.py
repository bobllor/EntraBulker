from msal import PublicClientApplication
from logger import Log
from typing import Any
from support.types import Response
import requests
import support.utils as utils
from core.graph_types import CreateUserJson, JsonHeaders, RequestErrorResponse

GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"
GRAPH_CREATE_USER_URL: str = f"{GRAPH_BASE_URL}/users"
GRAPH_ME_URL: str = f"{GRAPH_BASE_URL}/me"

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

        # least privilege scope that allows writing to entra, do not change!
        self._scopes: list[str] = ["User.ReadWrite.All"]
    
    def is_authenticated(self) -> Response:
        '''Checks if the client is authenticated. It will return a Response with the
        status of the authentication in content.
        '''
        res: Response = utils.generate_response("success", message="Authenticated", content=True)

        headers: JsonHeaders = {
            "authorization": self.bearer,
        }

        getres: requests.Response = requests.get(GRAPH_ME_URL, headers=headers) 
        json: dict[str, Any] = getres.json()

        if not getres.ok:
            err: RequestErrorResponse = self.get_error(json)

            self.log.warning(f"Failed to check authentication status: {err} | Code: {err.code} | Message: {err.message}")

            return utils.generate_response("error", message="Not authenticated", content=False)

        return res

    def authenticate(self) -> Response:
        '''Authenticates the client and retrieves the token for use in requests.'''
        res: Response = utils.generate_response(message="Successfully authenticated")
        self.log.info("Starting authentication process for Graph API")

        app: PublicClientApplication = PublicClientApplication(
            self._client_id,
            authority=self._auth_url,
        )

        if self.token is None:
            timeout_seconds: int = 300
            res: dict[str, Any] = app.acquire_token_interactive(self._scopes, timeout=timeout_seconds)
            token_key: str = "access_token"
            
            if token_key in res:
                self.token = res.get(token_key)
                self.bearer = f"Bearer {self.token}"
            else:
                errorStr: str = f"error={res.get('error')};desc={res.get('error_description')};id={res.get('correlation_id')}"
                self.log.warning(
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
    
    def create_users(self, users: list[CreateUserJson]) -> Response:
        '''Sends a POST request and creates the users. Errors that occur will not interrupt other users
        given in the list but will be logged.

        Any error that will occur automatically will mark the Response as an error.
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
            post_res: requests.Response = requests.post(GRAPH_CREATE_USER_URL, json=user_json, headers=headers)
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
            end_res["status"] = "error"
            end_res["message"] = f"Failed to add {len(failed_users)}/{len(users)} user(s) with Graph API"
        
        post_user_info["created users"]["Count"] = len(created_users)
        post_user_info["failed users"]["Count"] = len(failed_users)
        
        self.log.debug(f"POST users created: {post_user_info}")
        
        return end_res
    
    def get_error(self, d: dict[str, Any]) -> RequestErrorResponse:
        '''Parses a dictionary and creates a new RequestErrorResponse.'''
        code: str = utils.get_key(d, "code") or ""
        err_msg: str = utils.get_key(d, "message") or ""
        date: str = utils.get_key(d, "date") or ""
        request_id: str = utils.get_key(d, "request-id") or ""

        err = RequestErrorResponse(code, err_msg, date, request_id)
        
        return err