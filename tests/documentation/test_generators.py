from unittest import TestCase

from rest_framework.views import APIView

from documentation.generators import WhiteListedViewsEndpointEnumerator


class WhiteListedViewsEndpointEnumeratorTest(TestCase):

    def test_get_allowed_views_by_using_allowed_views_property(self):
        class PublicEndpointEnumerator(WhiteListedViewsEndpointEnumerator):
            allowed_views = ('full.view.Path', 'anohter.view.Class')

        self.assertEqual(PublicEndpointEnumerator.allowed_views, PublicEndpointEnumerator().get_allowed_views())

    def test_get_allowed_views_by_using_modified_get_allowed_views_method(self):
        class PublicEndpointEnumerator(WhiteListedViewsEndpointEnumerator):
            allowed_views = ('full.view.Path', 'anohter.view.Class')

            def get_allowed_views(self):
                return 'app.view.FirstView', 'app.view.SecondView'

        enumerator = PublicEndpointEnumerator()
        method_result = enumerator.get_allowed_views()
        self.assertEqual(('app.view.FirstView', 'app.view.SecondView'), method_result)
        self.assertNotEqual(method_result, PublicEndpointEnumerator.allowed_views)

    def test_filtering_views_by_allowed_view_names(self):
        class AllowedApiView(APIView):
            pass

        class PrivateApiView(APIView):
            pass

        allowed_view_full_path = '{}.{}'.format(AllowedApiView.__module__, AllowedApiView.__name__)

        class PublicEndpointEnumerator(WhiteListedViewsEndpointEnumerator):
            allowed_views = (allowed_view_full_path, 'anohter.view.Class')

        args_list = (
            {
                'expected_result': True,
                'args': ('/public-view-path/', AllowedApiView.as_view(), 'safe_app', '', 'safe_app_url_name')
            },
            {
                'expected_result': False,
                'args': ('/private-view-path/', PrivateApiView.as_view(), 'internal_app', '', 'internal_app_url_name')
            }
        )

        enumerator = PublicEndpointEnumerator()
        for row in args_list:
            result = enumerator.should_include_endpoint(*row['args'])
            view_name = row['args'][1].view_class.__name__
            expected_result = row['expected_result']
            self.assertTrue(result == expected_result,
                            'Expected result for view named {} is {}'.format(view_name, expected_result))
