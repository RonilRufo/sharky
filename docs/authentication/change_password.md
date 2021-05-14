# Change Password
----------------
This is a documentation for the queries and mutations used in `Change Password` page.

- ### Change Password
    - **Overview**
        - Enables users to change their existing passwords.
    - **Permissions**
        - This requires an authenticated user.
    - **Sample Request**
        ```
            POST /graphql/

            mutation (
                passwordChange(oldPassword: "oldpassword",
                               newPassword1: "thisisanewpassword",
                               newPassword2: "thisisanewpassword") {
                    success
                    errors
                    token
                }
            )
        ```
    - **Sample Response**
        ```
            {
                'data': {
                    'passwordChange': {
                        'success': True,
                        'errors': None
                        'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IndpbGxpYW1zc3VlIiwiZXhwIjoxNTk3MTQ5NTY5LCJvcmlnSWF0IjoxNTk3MTQ5MjY5fQ.ztXsvJSCf9dxVm1Gc7nzCWBbJOnaFY-eVa402qHLiX8'
                    }
                }
            }
        ```
