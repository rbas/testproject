from collections import OrderedDict
from unittest import TestCase
from unittest.mock import Mock

from django.http import HttpRequest
from drf_yasg.inspectors import BaseInspector
from drf_yasg.openapi import ReferenceResolver, Schema, TYPE_OBJECT
from rest_framework import status, serializers
from rest_framework.request import Request
from rest_framework.views import APIView

from documentation.schema import guess_response_status, NoSchemaTitleInspector, ElexApisAutoSchema


class GuessResponseStatusTest(TestCase):

    def test_post_method(self):
        self.assertEquals(status.HTTP_200_OK, guess_response_status('post'))

    def test_post_delete(self):
        self.assertEquals(status.HTTP_204_NO_CONTENT, guess_response_status('delete'))

    def test_post_get(self):
        self.assertEquals(status.HTTP_200_OK, guess_response_status('get'))

    def test_post_put(self):
        self.assertEquals(status.HTTP_200_OK, guess_response_status('put'))


class NoSchemaTitleInspectorTest(TestCase):

    def test_remove_title_from_schema(self):
        request = Request(HttpRequest())
        inspector = NoSchemaTitleInspector(APIView(), '/some/path/', 'method',
                                           ReferenceResolver(), request, BaseInspector)

        schema = Schema('Schema title', 'Schema description', TYPE_OBJECT)
        result = inspector.process_result(schema, 'some_method_name', self)

        self.assertFalse(hasattr(result, 'title'), 'Schema cannot to contain property title')
        self.assertTrue(hasattr(result, 'description'), 'Schema must to contain property description')

        self.assertEquals(id(schema), id(result), 'Result of method named process_result must return same instance '
                                                  'of included object.')


class ElexApisAutoSchemaTest(TestCase):

    def test_get_operation_id(self):
        view = Mock(spec=APIView)
        reference_resolver = Mock(spec=ReferenceResolver)
        request = Mock(spec=Request)
        path = '/some-path-with-parameter/{id}/'

        schema = ElexApisAutoSchema(view, path, 'post', reference_resolver, request, {})

        result = schema.get_operation_id(('some', 'unused', 'tags'))

        self.assertEqual(path, result, 'Operation id must be same like view path.')

    def _do_get_view_serializer_test(self, view_class):
        view = view_class()
        reference_resolver = Mock(spec=ReferenceResolver)
        request = Mock(spec=Request)
        path = '/some-path-with-parameter/{id}/'

        schema = ElexApisAutoSchema(view, path, 'post', reference_resolver, request, {})

        serializer_class = serializers.Serializer
        obtained_serializer = schema.get_view_serializer()

        self.assertIsInstance(obtained_serializer, serializer_class,
                              'Serializer must be subclass of {} not {}'.format(serializer_class.__class__,
                                                                                obtained_serializer.__class__))

    def test_get_view_serializer_by_using_get_serializer_method(self):
        class TestApiView(APIView):
            def get_serializer(self):
                return serializers.Serializer()

        self._do_get_view_serializer_test(TestApiView)

    def test_get_view_serializer_by_using_serializer_class_property(self):
        class TestApiView(APIView):
            serializer_class = serializers.Serializer

        self._do_get_view_serializer_test(TestApiView)

    def test_get_responses_with_default_http_response_status_defined(self):
        class TestApiView(APIView):
            default_http_response_status = 42

        view = TestApiView()
        reference_resolver = Mock(spec=ReferenceResolver)
        request = Mock(spec=Request)
        path = '/some-path-with-parameter/{id}/'

        schema = ElexApisAutoSchema(view, path, 'post', reference_resolver, request, {})

        responses = schema.get_default_responses()
        self.assertIsInstance(responses, OrderedDict, 'Result must be instance of OrderedDict')
        self.assertEqual(next(iter(responses)),
                         str(TestApiView.default_http_response_status),
                         'First key in OrderedDict must be equal to value `default_http_response_status`')

    def test_get_default_response_serializer_with_defined_property_response_serializer_class(self):
        class TestApiView(APIView):
            response_serializer_class = serializers.Serializer

        view = TestApiView()
        reference_resolver = Mock(spec=ReferenceResolver)
        request = Mock(spec=Request)
        path = '/some-path-with-parameter/{id}/'

        schema = ElexApisAutoSchema(view, path, 'post', reference_resolver, request, {})
        obtained_serializer = schema.get_default_response_serializer()

        self.assertIsInstance(obtained_serializer, TestApiView.response_serializer_class)

    def test_get_default_response_serializer_with_wrapped_response_structure_method(self):
        def response_structure_method_wrapper(self, serializer):
            return serializer

        class TestApiView(APIView):
            response_serializer_class = serializers.Serializer
            response_structure_method = response_structure_method_wrapper

        view = TestApiView()
        reference_resolver = Mock(spec=ReferenceResolver)
        request = Mock(spec=Request)
        path = '/some-path-with-parameter/{id}/'

        schema = ElexApisAutoSchema(view, path, 'post', reference_resolver, request, {})
        obtained_serializer = schema.get_default_response_serializer()

        self.assertIsInstance(obtained_serializer, TestApiView.response_serializer_class)
