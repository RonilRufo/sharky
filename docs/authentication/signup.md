# Signup
----------------
This is a documentation for the queries and mutations used in `Signup` page.

- ### Signup
    - **Overview**
        - Enables users to register.
    - **Sample Request**
        ```
            POST /graphql/

            mutation (
                register(email: "user@email.com", password1: "mypassword", password2: "mypassword) {
                    success
                    errors
                }
            )
        ```
    - **Sample Response**
        ```
            {
                'data': {
                    'register': {
                        'success': True,
                        'errors': None
                    }
                }
            }
        ```
