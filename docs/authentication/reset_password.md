# Reset Password
----------------
This is a documentation for the queries and mutations used in `Reset Password` page.

- ### Reset Password
    - **Overview**
        - Enables users to reset their passwords without supplying the old password. This requires the `token` passed via the forgot password email.
    - **Sample Request**
        ```
            POST /graphql/

            mutation (
                passwordReset(token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
                              newPassword1: "thisisanewpassword",
                              newPassword2: "thisisanewpassword") {
                    success
                    errors
                }
            )
        ```
    - **Sample Response**
        ```
            {
                'data': {
                    'passwordReset': {
                        'success': True,
                        'errors': None
                    }
                }
            }
        ```
