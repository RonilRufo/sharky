import json


class GraphQLAuthErrorMiddleware:
    """
    Extracts the errors from inner child of the response then moves
    it to the parent key. If errors exist, status will be 400 BAD REQUEST.

    By default, `django-graphql-auth` always returns a 200 OK response
    even if there are errors in the request. This middleware will override
    that feature by retrieving the errors(if exists) from the response then
    assigns 400 BAD REQUEST status into it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        response = self.extend_response_processing(response)

        return response

    def extend_response_processing(self, response):
        try:
            content = json.loads(response.content)
        except Exception:
            content = None

        if content and content.get('data', None):
            data = content.get('data', None)
            keys = data.keys()
            for key in keys:
                if data[key]:
                    try:
                        errors = data[key].get('errors', None)
                    except Exception:
                        errors = None

                    if errors:
                        response_data = {
                            'errors': errors,
                            'data': data
                        }
                        response.content = json.dumps(response_data)
                        response.status_code = 400

        return response
