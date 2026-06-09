# Microsoft Graph Settings

Starting as of `EntraBulker v2.0.0`, Microsoft Graph is supported, enabling *automated user creation*
directly into the tenant instead of manually uploading a CSV file.
Unlike the manual provisioning, the *member type* of the users can be toggled between
*Guest* or *Member*.

In order for Microsoft Graph to be used, you will need:
- A registered application on the tenant's Entra ID
- Your account has the `User.ReadWrite.All` permission, or in other words able to create, delete, and modify users
in Entra ID
- The registered application client ID and the tenant ID of your tenant

## Entra ID Application

An Entra ID application is required for EntraBulker to build the connection between the application
and the tenant. This enables access Microsoft services and APIs.

### Registration

Microsoft has its own dedicated article for 
[registering an application](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app).
It covers all the essentials for registering the application. The application should be made as *single tenant only*.

### Redirect URI

The redirect URI must be added in the application settings. This allows the application to send a
authorization login request, enabling the communication for the tokens and authorization codes back
to the client.
Microsoft has an article covering 
[how to add a redirect URI](https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-redirect-uri).

The application platform to choose is the `Mobile and desktop applications`, the redirect URI should be 
added based on this platform option.

The redirect URI is *dependent on your requirements*. If you are unsure what to choose, use `http://localhost:8400`.

### Scopes

EntraBulker *creates new users* in the tenant, therefore the minumum scope required is `User.ReadWrite.All`.
Since the application uses *delegated permissions*, the account used to login for authentication *must be able*
to perform CRUD operations on a tenant.

The scope *must be configured* in the application settings, which accessed via `Expose an API` > `Add a scope`.
Microsoft has an article on 
[how to configure the scope](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-configure-app-expose-web-apis).

## EntraBulker Settings

### Enable Graph

Used to enable Graph for user creation. By default this is disabled.
This requires the application to be authenticated in order to fully utilize Graph.

If not authenticated, then this will do nothing.

### Client Application ID

The client ID of the registered application. This is required in order to authenticate
the application for Graph use.

### Tenant ID

The ID of the tenant the application is registered in and the users you are attempting to
create in. This is required for authorization.

### Member Type Domain CSV

This is only applicable if the `User Type` is set to `Guest`. It is expected to be a
*CSV style string* of domain names, e.g. `company.one.com,@company.two.com,company.three.com`.

It is used to ensure that users with these domains are created with **Member type** access.

This is *spelling sensitive*, and the value must match the exact ending as the domain you are
expecting. The `@` symbol is not necessary, as long as the end string matches the given CSV strings.

### User Type

Toggles the *user type* of the created user when added via Graph. This represents the level of access the user has in your
tenant. To read more about this, read the article [here](https://learn.microsoft.com/en-us/entra/external-id/user-properties).

By default users are created as `Member` for full access in your tenant, but there may be times where `Guest` type is needed.
This options allows you to toggle between the two types for all users created from the files.

By default it will create users as `Guest`, for least privilege. You can change this to `Member` or for more advanced
filtering, use the `Member Type Domain CSV` to keep both `Guest` and `Member` type assignments.

### Sign In

A login button used to start the authentication process for the application and your delegated permissions.
The authenication process has a *timeout of two minutes*, failure to authenticate within this time period
will cancel the process.

If properly configured, clicking on the `Sign in` button will open your browser to login using the Microsoft
account *associated with your tenant*.
Upon success, it will redirect to the redirect URI and your application will be authenticated, indicated by the
`Status: ...` value.

Once signed in for the first time, your token is cached to an encrypted file (fallbacks to plain text on failure).
It enables *signing back in without the browser flow* to reauthenticate using this cached token.

The checkbox `Stay signed in` can be used to automatically login upon the application load. This allows
you to not have to go into settings to reauthenticate. By default, this is enabled.

### Sign Out

This option signs out your application from Graph. It does not delete the cache, and you can sign back in with
no issue.

Only used for if you want to not use Graph.

### Clear Cache

> WARNING
>
> This will remove the cached data and you will need to reauthenticate.

Removes all cached files and force a new reauthentication. This is used if you need to login
to a different account or you want to remove cached files.