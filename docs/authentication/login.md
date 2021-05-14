# Login
----------------
This is a documentation for the queries and mutations used in `Login` page.

- ### Login
    - **Overview**
        - Enables users to login.
    - **Sample Request**
        ```
            POST /graphql/

            mutation (
                tokenAuth(email: "user@email.com", password: "mypassword") {
                    token
                    success
                    user {
                        email
                    }
                    errors
                }
            )
        ```
    - **Sample Response**
        ```
            {
                'data': {
                    'tokenAuth': {
                        'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IndpbGxpYW1zc3VlIiwiZXhwIjoxNTk3MTQ5NTY5LCJvcmlnSWF0IjoxNTk3MTQ5MjY5fQ.ztXsvJSCf9dxVm1Gc7nzCWBbJOnaFY-eVa402qHLiX8',
                        'success': True,
                        'user': {
                            'email': 'user@email.com'
                        },
                        'errors': None
                    }
                }
            }
        ```
