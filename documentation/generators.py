from drf_yasg.generators import OpenAPISchemaGenerator, EndpointEnumerator


class WhiteListedViewsEndpointEnumerator(EndpointEnumerator):
    """
    Filter API endpoints based on own property `allowed_views`


    Example:
        class MyPublicApiEndpointEnumerator(WhiteListedViewsEndpointEnumerator):
            allowed_views = ('api.views.dist_ids.DistIds', 'apiv3.views.signups.SignupsV3p1View')

    If view is not in the list it will NOT be used in API documentation.
    """
    allowed_views = None  # n-tice of strings with full paths to allowed Views

    def should_include_endpoint(self, path, callback, app_name='', namespace='', url_name=None):
        class_name = self._gen_class_name(callback)
        allowed_views = self.get_allowed_views()
        if class_name not in allowed_views:
            return False

        return super().should_include_endpoint(path, callback, app_name, namespace, url_name)

    def _gen_class_name(self, callback) -> str:
        try:
            return '{}.{}'.format(callback.view_class.__module__, callback.view_class.__name__)
        except AttributeError:
            # Expected error
            return ''

    def get_allowed_views(self):
        return self.allowed_views
