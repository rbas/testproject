from collections import OrderedDict

from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.inspectors import SwaggerAutoSchema, FieldInspector
from drf_yasg.inspectors.base import call_view_method
from drf_yasg.utils import force_serializer_instance, get_serializer_class
from rest_framework import status


def guess_response_status(method: str) -> int:
    """
    Returns HTTP status code based on method type

    :param method: HTTP method name
    :return: HTTP status code
    """
    if method == 'post':
        return status.HTTP_200_OK
    elif method == 'delete':
        return status.HTTP_204_NO_CONTENT
    else:
        return status.HTTP_200_OK


class NoSchemaTitleInspector(FieldInspector):
    """
    Remove the `title` attribute of all Schema objects
    """
    def process_result(self, result, method_name, obj, **kwargs):
        if isinstance(result, openapi.Schema.OR_REF):
            # traverse any references and alter the Schema object in place
            schema = openapi.resolve_ref(result, self.components)
            schema.pop('title', None)

        return result


class ElexApisAutoSchema(SwaggerAutoSchema):
    """
    API Documentation generator

    Overwriting default class with tweeks for our view classes. For view information see documentation in methods.
    """
    field_inspectors = [NoSchemaTitleInspector] + swagger_settings.DEFAULT_FIELD_INSPECTORS

    def get_default_response_serializer(self):
        """Return the default response serializer for this endpoint. This is derived from either the ``request_body``
        override or the request serializer (:meth:`.get_view_serializer`).

        Method works with two properties which allow to overwrite default behavior.
        First one is `response_serializer_class` if it is defined method will returns that value, but value must
        be instance of `rest_framework.serializers.Serializer`. If is defined also property named
        `response_structure_method` and value is callable, this method will put value from `response_serializer_class`
        into like parameter. It is useful for wrapping default response serializer with response structured data.

        :return: response serializer, :class:`.Schema`, :class:`.SchemaRef`, ``None``
        """
        if hasattr(self.view, 'response_serializer_class'):
            serializer_class = get_serializer_class(self.view.response_serializer_class)
            if hasattr(self.view, 'response_structure_method'):
                response_structure_method = self.view.response_structure_method

                assert callable(response_structure_method), 'response_structure_method expects a callable, ' \
                                                            'not %s' % type(response_structure_method).__name__

                serializer_class = response_structure_method(serializer_class)
            return force_serializer_instance(serializer_class)
        else:
            return super().get_default_response_serializer()

    def get_default_responses(self):
        """
        Overwrite http status code

        If view have property named `default_http_response_status` then this method will using that value for
        http status code.
        """
        responses = super().get_default_responses()
        method = self.method.lower()
        http_response_status = guess_response_status(method)

        if hasattr(self.view, 'default_http_response_status'):
            http_response_status = self.view.default_http_response_status

        parts = responses.popitem()

        return OrderedDict({str(http_response_status): parts[1]})  # Remove DRF-YASG default http status code

    def get_view_serializer(self):
        """Return the serializer as defined by the view's ``get_serializer()`` method.

        Allow to get view serializer with two another ways.
        1) defined method named `get_serializer()`
        2) defined property named `serializer_class`
           (its value must be subclass of rest_framework.serializers.Serializer)

        :return: the view's ``Serializer``
        :rtype: rest_framework.serializers.Serializer
        """
        if hasattr(self.view, 'get_serializer'):
            return call_view_method(self.view, 'get_serializer')
        elif hasattr(self.view, 'serializer_class'):
            serializer = get_serializer_class(self.view.serializer_class)
            return serializer()
        else:
            return super().get_view_serializer()

    def get_operation_id(self, operation_keys):
        return self.path
