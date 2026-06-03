from msal import PublicClientApplication, SerializableTokenCache
from msal.oauth2cli.oauth2 import BrowserInteractionTimeoutError
from logger import Log
from typing import Any, Callable, TypeVar, ParamSpec
from support.types import Response
from core.types.graph import CreateUserJson, JsonHeaders, RequestErrorResponse, GraphAccountCacheReader
from core.graph_tils.writer import TokenCacheWriter
from pathlib import Path
from core.json_reader import Reader
from functools import wraps
import json
import requests
import support.utils as utils

GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"
GRAPH_CREATE_USER_URL: str = f"{GRAPH_BASE_URL}/users"
GRAPH_ME_URL: str = f"{GRAPH_BASE_URL}/me"

REQ_TIMEOUT: int = 20
P = ParamSpec("P")
T = TypeVar("T")

def requests_handler(f: Callable[P, T]) -> Callable[P, T]:
    '''Decorator used to wrap requests methods in a try-except and logs with
    errors if one occurs.

    The method must be a class with a logging instance self.log, and the method must return a Response.

    Any error exceptions will return the error `status`, the error `message`, and a None `content`.
    '''
    @wraps(f)
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

def authenticate_middleware(f: Callable[P, Response]) -> Callable[P, Response]:
    '''Middleware used to handle authentication for protected methods.
    
    The wrapped function must be from a class with the following:
        - authenticate() -> Response
    
    If the function does not have the above then unexpected errors will occur.
    '''
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        auth_res: Response = self.authenticate()
        if auth_res["status"] == "error":
            return auth_res

        res: Response = f(self, *args, **kwargs)

        return res
    
    return wrapper

CACHE_NAME: str = ".msaccount-cache.json"
DEFAULT_CACHE_MAP: GraphAccountCacheReader = {
    "account_cache": [],
    "recent_username": "",
}

class Graph:
    '''Class used for Microsoft Graph based operations.'''
    def __init__(self, client_id: str= "", tenant_id: str = "", *, project_root: Path, log: Log = None):
        '''
        Parameters
        ----------
            client_id: str
                The client application ID of the registered app in Entra ID.
                By default it is an empty string.

            tenant_id: str
                The directory tenant ID of the Entra ID tenant being targeted.
                By default it is an empty string.
            
            project_root: Path
                The project root path directory. It will be used to write and retrieve
                the accounts cache and the token cache.

            log: Log
                The logging object. By default it is None and will initialize
                an stdout based Log.
        '''
        self._client_id: str = client_id
        self._tenant_id: str = tenant_id

        self.log: Log = log or Log()

        self._auth_url: str = f"https://login.microsoftonline.com/{self._tenant_id}"

        # set inside authenticate
        self.app: PublicClientApplication = None
        
        config_path: Path = project_root / "config"

        # the json reader, not related to the token cache writer
        self.cache_reader = Reader(
            config_path / CACHE_NAME, 
            logger=self.log,
            project_root=project_root,
            defaults=DEFAULT_CACHE_MAP,
        )

        # token cache writer and reader. by default it will be encrypted, but plain text is a
        # fall back. 
        self.token_cache_writer: TokenCacheWriter = TokenCacheWriter(config_path, log=self.log)

        # set in authenticate
        self.access_token: str = ""

        # set inside the first call of authenticate
        self.token_cache: SerializableTokenCache = self.get_token_cache()

        # least privilege scope that allows writing to entra, do not change!
        self._scopes: list[str] = ["User.ReadWrite.All"]

    def authenticate(self) -> Response:
        '''
        Authenticates the client and retrieves the token for use in requests. This is only
        required to be called once to log in for authentication.
        Afterwards, it will be used as middleware for protected methods.

        The account cache will be used first, which if it fails will attempt an interactive browser.
        Upon successful authentication, the cache will be written to with the logged in user
        and the cache of the account.

        The token will be updated upon a successful authentication. 
        '''
        res: Response = utils.generate_response(message="Successfully authenticated")
        self.log.info("Starting authentication process for Graph API")

        token_key: str = "access_token"
        cache: GraphAccountCacheReader = self.cache_reader.get_content()
        auth_url: str = f"https://login.microsoftonline.com/{self._tenant_id}"

        try:
            app: PublicClientApplication = self.app
            if not self.app:
                app = PublicClientApplication(
                    self._client_id,
                    authority=auth_url,
                    token_cache=self.token_cache,
                )

            result: dict[str, Any] | None = self._authenticate_with_account(app)
            if result is not None:
                self.log.info("Existing cached token found, extracting token")
                self.access_token = result.get(token_key, "")
            else:
                self.log.info("No cached token found")
                timeout_seconds: int = 120

                try:
                    result = app.acquire_token_interactive(self._scopes, timeout=timeout_seconds)
                except BrowserInteractionTimeoutError:
                    self.log.info(f"Authentication timeout reached: User did not complete the flow in time")

                    return utils.generate_response("error", message="Authentication timed out")

                if token_key in result:
                    self.log.info("Successfully authenticated, extracting token")
                    self.access_token = result.get(token_key, "")

                    accounts: list[dict[str, Any]] = app.get_accounts()
                    if len(cache["account_cache"]) != len(accounts) and len(accounts) > 0:
                        self.cache_reader.update("account_cache", accounts)
                        self.cache_reader.update("recent_username", accounts[-1].get("username"))
                else:
                    errorStr: str = f"error={result.get('error')};desc={result.get('error_description')};id={result.get('correlation_id')}"
                    self.log.error(
                        f"Failed to authenticate Graph API | {errorStr}"
                    )
                    res = utils.generate_response("error", message="Failed to authenticate")

                    return res
                
                self.log.debug(f"Access token length: {len(self.access_token)}")

            self.app = app
            # needs to be rewritten every authentication
            self.save_token_cache(self.token_cache.serialize())

            return res

        except ValueError as e:
            self.log.error(f"Authority URL: {auth_url} | Tenant ID: {self._tenant_id} | {str(e)}")

            return utils.generate_response("error", message="Authentication failed due to invalid tenant")

        except Exception as e:
            self.log.error(f"An unknown exception occurred ({type(e)}): {str(e)}")

            return utils.generate_response("error", message="An unknown error occurred while authenticating")
    
    def _authenticate_with_account(self, app: PublicClientApplication) -> dict[str, Any] | None:
        '''Authenticates with the most recent account in the cache and return the result.
        
        If there is no result, then it will return `None`.
        '''
        account: dict[str, Any] = self.get_cache_account()
        self.log.debug(f"Most recent cached account: {account}")
        result: dict[str, Any] | None = app.acquire_token_silent(self._scopes, account)

        return result
    
    def get_cache_account(self) -> dict[str, Any] | None:
        '''Retrieves the account from the cache to use for the authentication process. 
        
        If *multiple accounts* are found in the cache, it will use the **most recently
        logged in account**. 
        If the most recent account cannot be found in the cache, then it 
        will **use the latest entry in the cache**.
        If *no accounts exist* in the cache, then it will return `None`.

        This requires self.cache_reader to exist, if it is not initialized then it will 
        return `None`.
        '''
        if not self.cache_reader:
            self.log.warning("Cache Reader was not initialized")
            return None

        reader: GraphAccountCacheReader = self.cache_reader.get_content()
        cache: list[dict[str,Any]] = reader.get("account_cache")
        if len(cache) == 0:
            self.log.info("No accounts found in cache")
            return None
        
        recent_user: str = reader.get("recent_username")
        for acc in cache:
            if acc.get("username") == recent_user:
                return acc

        # use the latest entry in the cache if the user is not found
        most_recent_account: dict[str, Any] = cache[-1]
        self.cache_reader.update("recent_username", most_recent_account.get("username", ""))

        return most_recent_account
    
    def save_token_cache(self, content: dict[str, Any] | str):
        '''Writes the content to the persistent cache for the token. Content can be
        a dictionary or string.
        '''
        data: str = json.dumps(content) if isinstance(content, dict) else content
        self.token_cache_writer.save(data)

        self.log.info("Saved data to token cache")
    
    def get_token_cache(self) -> SerializableTokenCache:
        '''Retrieves the token cache from the persistent cache file.
        
        If the token cache does not exist or if an error occurs
        while deserializing, it will return a default token cache. 
        '''
        token_cache: SerializableTokenCache = SerializableTokenCache()

        if not self.token_cache_writer.exists():
            return token_cache

        cache_str: str = self.token_cache_writer.load()

        try:
            token_cache.deserialize(cache_str)
            self.log.info("Deserialized token cache")
        except Exception:
            self.log.exception("Failed to load cache data")
            self.log.info("Using an empty token cache due to an error while loading")

            return token_cache

        return token_cache

    def clear_cache(self) -> Response:
        '''Clears the accounts and token cache from Graph. This does not logout the account,
        that must be handled separately.
        '''
        self.log.info("Starting cache clearing process for Graph")
        account: dict[str, Any] = self.get_cache_account()
        account_cache: GraphAccountCacheReader = self.cache_reader.get_content()

        if self.app:
            if account is not None:
                self.app.remove_account(account)

        new_account_cache: list[dict[str, Any]] = []
        for d in account_cache["account_cache"]:
            if account_cache["recent_username"] != d.get("username"):
                new_account_cache.append(d)

        self.log.debug(f"New account cache: {new_account_cache}")

        account_cache["account_cache"] = new_account_cache
        account_cache["recent_username"] = ""

        self.cache_reader.write(account_cache)
        self.token_cache_writer.save("")

        return utils.generate_response("success", message="Successfully signed out from Graph")
    
    @requests_handler 
    @authenticate_middleware
    def create_users(self, users: list[CreateUserJson]) -> Response:
        '''Sends a POST request and creates users in the tenant. 

        Errors that occur will not interrupt other users given in the list but will be logged.
        
        If all users given failed to POST for whatever reason, then it will return an *error*. 
        If there are a handful of failed POST requests, then it will return a *warning*. 
        '''
        end_res: Response = utils.generate_response(message=f"Created users")

        headers: JsonHeaders = {
            "authorization": f"Bearer {self.access_token}",
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