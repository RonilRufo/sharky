# Verify Account
----------------
This is a documentation for the queries and mutations used in `Verify Account` page.

- ### Verify Account
    - **Overview**
        - Enables users to verify their accounts. This requires the `token` passed via the verify account email right after signing up.
    - **Sample Request**
        ```
            POST /graphql/

            mutation (
                verifyAccount(token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9") {
                    success
                    errors
                }
            )
        ```
    - **Sample Response**
        ```
            {
                'data': {
                    'verifyAccount': {
                        'success': True,
                        'errors': None
                    }
                }
            }
        ```
