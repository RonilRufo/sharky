# Forgot Password
----------------
This is a documentation for the queries and mutations used in `Forgot Password` page.

- ### Forgot Password
    - **Overview**
        - Sends instructions to the given `email` on how to reset his/her password.
    - **Sample Request**
        ```
            POST /graphql/

            mutation (
                sendPasswordResetEmail(email: "user@email.com") {
                    success
                    errors
                }
            )
        ```
    - **Sample Response**
        ```
            {
                'data': {
                    'sendPasswordResetEmail': {
                        'success': True,
                        'errors': None
                    }
                }
            }
        ```
