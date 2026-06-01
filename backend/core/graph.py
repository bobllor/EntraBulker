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

        error_count: int = 0
        for user_json in users:
            post_res: requests.Response = requests.post(GRAPH_CREATE_USER_URL, json=user_json, headers=headers)
            data: dict[str, Any] = post_res.json()

            if not post_res.ok:
                # TODO: parse error
                error: RequestErrorResponse = self.get_error(data)
                self.log.warning(f"Failed to create user {user_json['givenName']}: {error}")
                error_count += 1

            self.log.debug(f"POST response: {data}")
        
        if error_count > 0:
            end_res["status"] = "error"
            end_res["message"] = f"Failed to add {error_count}/{len(users)} user(s) over Graph API"
        
        return end_res

    def create_user(self) -> Response:
        '''Sends a POST request and creates the user.'''
        end_res: Response = utils.generate_response(message=f"Created user")
        headers: JsonHeaders = {
            "authorization": self.bearer,
            "content-type": "application/json"
        }

        json_data: CreateUserJson = {
            "accountEnabled": True,
            "displayName": "",
            "mailNickname": "",
            "userPrincipalName": "",
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": "",
            },
            "userType": "",
        }

        post_res: requests.Response = requests.post(GRAPH_CREATE_USER_URL, json=json_data, headers=headers)

        self.log.debug(f"Post response code: {post_res.status_code}")

        if not post_res.ok:
            # TODO: parse error
            self.log.warning(f"Failed to create user")
            err_res: Response = utils.generate_response("error", message=f"Failed to create user", content=False)

            return err_res
        
        return end_res
    
    def get_error(self, d: dict[str, Any]) -> RequestErrorResponse:
        '''Parses a dictionary and creates a new RequestErrorResponse.'''
        code: str = utils.get_key(d, "code") or ""
        err_msg: str = utils.get_key(d, "message") or ""
        date: str = utils.get_key(d, "date") or ""
        request_id: str = utils.get_key(d, "request-id") or ""

        err = RequestErrorResponse(code, err_msg, date, request_id)
        
        return err