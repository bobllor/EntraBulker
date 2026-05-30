from msal import PublicClientApplication
from logger import Log
from typing import Any
from backend.support.types import Response
import requests
import backend.support.utils as utils
from backend.core.graph_types import CreateUserJson, JsonHeaders

GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"
GRAPH_CREATE_USER_URL: str = f"{GRAPH_BASE_URL}/users"

class Graph:
    '''Class used for Microsoft Graph based operations.'''
    def __init__(self, client_id: str, tenant_id: str, *, log: Log = None):
        self._client_id: str = client_id
        self._tenant_id: str = tenant_id

        self.log: Log = log or Log()

        self._auth_url: str = f"https://login.microsoftonline.com/{self._tenant_id}"

        self.app: PublicClientApplication = PublicClientApplication(
            self._client_id,
            authority=self._auth_url,
        )

        self.token: str = None
        # set in authenticate on succcessful token retrieval
        self.bearer: str = None

        # least privilege scope that allows writing to entra, do not change!
        self._scopes: list[str] = ["User.ReadWriteAll"]
    
    def is_authenticated(self) -> Response:
        '''Checks if the client is authenticated.'''
        res: Response = utils.generate_response("success", message="Authenticated", content=True)

        return res

    def authenticate(self) -> Response:
        '''Authenticates the client and retrieves the token for use in requests.'''
        res: Response = utils.generate_response(message="Successfully authenticated")
        self.log.info("Starting authentication process for Graph API")

        if self.token is None:
            timeout_seconds: int = 300
            res: dict[str, Any] = self.app.acquire_token_interactive(self._scopes, timeout=timeout_seconds)
            token_key: str = "access_token"
            
            if token_key in res:
                # default to None so auth can rerun again, if it occurs
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
            }
        }

        post_res: requests.Response = requests.post(GRAPH_CREATE_USER_URL, json=json_data, headers=headers)

        self.log.debug(f"Post response code: {post_res.status_code}")

        if not post_res.ok:
            # TODO: parse error
            self.log.warning(f"Failed to create user")
            err_res: Response = utils.generate_response("error", message=f"Failed to create user", content=False)

            return err_res
        
        return end_res