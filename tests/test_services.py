try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import six
from unittest import TestCase

from django import forms
from django.db import models

from service_objects.errors import InvalidInputsError
from service_objects.services import Service, ModelService


class FooModel(models.Model):
    one = models.CharField(max_length=1)

    class Meta:
        app_label = 'tests'


class FooService(Service):
    bar = forms.CharField(required=True)


class MockService(Service):
    bar = forms.CharField(required=True)


class NoDbTransactionService(Service):
    db_transaction = False


MockService.process = Mock()
NoDbTransactionService.process = Mock()


class ServiceTest(TestCase):

    def test_base_class(self):
        MockService.execute({'bar': 'Hello'})

        MockService.process.assert_called_with()

    def test_process_implemented(self):
        with self.assertRaises(NotImplementedError):
            FooService.execute({'bar': 'Hello'})

    def test_fields(self):
        with self.assertRaises(InvalidInputsError):
            MockService.execute({})

        MockService.execute({'bar': 'Hello'})

    def test_invalid_inputs_error(self):
        with self.assertRaises(InvalidInputsError) as cm:
            MockService.execute({})

        self.assertIn('InvalidInputsError', repr(cm.exception))
        self.assertIn('bar', repr(cm.exception))
        self.assertIn('This field is required.', repr(cm.exception))

    @patch('service_objects.services.transaction')
    def test_db_transaction_flag(self, mock_transaction):

        NoDbTransactionService.execute({})
        assert not mock_transaction.atomic.return_value.__enter__.called

        MockService.execute({'bar': 'Hello'})
        assert mock_transaction.atomic.return_value.__enter__.called


class ModelServiceTest(TestCase):

    def test_auto_fields(self):

        class FooModelService(ModelService):
            class Meta:
                model = FooModel
                fields = '__all__'

        f = FooModelService()

        field_names = list(six.iterkeys(f.fields))
        self.assertEqual(1, len(field_names))
        self.assertEqual('one', field_names[0])

    def test_extra_fields(self):

        class FooModelService(ModelService):
            two = forms.CharField()

            class Meta:
                model = FooModel
                fields = '__all__'

        f = FooModelService()

        field_names = list(six.iterkeys(f.fields))
        self.assertEqual(2, len(field_names))
        self.assertEqual('one', field_names[0])
        self.assertEqual('two', field_names[1])
