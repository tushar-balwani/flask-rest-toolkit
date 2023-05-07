"""
Basic building blocks for generic class based apis.
"""
from http import HTTPStatus

from flask_restful import Resource
from flask import jsonify
from marshmallow.exceptions import ValidationError

from rest_toolkit.exceptions import FieldsMissingException


class BaseApiResource:
    """
    Init class for fields
    """
    db = None
    model = None
    serializer = None
    request = None
    resultset = None

    # default required fields for each method
    fields = {
        'post': ('request', 'serializer', 'model', 'db'),
        'get': ('serializer', 'resultset'),
        'put': ('request', 'serializer', 'resultset'),
        'patch': ('request', 'serializer', 'resultset'),
        'delete': ('resultset', 'db'),
    }

    def validate(self):
        """
        validate all required fields assigned
        :return:
        """
        missing_fields = []
        for field in self.fields.get(self.request.method.lower(), ()):
            if not getattr(self, field, None):
                missing_fields.append(field)

        if missing_fields:
            error_message = f"The following fields are missing: {', '.join(missing_fields)}"
            raise FieldsMissingException(error_message)


class CreateApiResource(BaseApiResource, Resource):
    """
    Create a model instance.
    """
    method_decorators = []

    def __init__(self, decorators):
        self.method_decorators = decorators

    def post(self):
        try:
            data = self.request.get_json()
            result = self.serializer.load(data)
            response = self.model(**result)
            self.db.session.add(response)
            self.db.session.commit()
            return self.serializer.dump(response), HTTPStatus.CREATED
        except ValidationError as e:
            return jsonify({'error': e.messages}), HTTPStatus.BAD_REQUEST


class ListApiResource(BaseApiResource, Resource):
    """
    List a resultset.
    """
    method_decorators = []

    def __init__(self, decorators):
        self.method_decorators = decorators

    def get(self):
        try:
            return self.serializer.dump(self.resultset), HTTPStatus.OK
        except ValidationError as e:
            return jsonify({'error': e.messages}), HTTPStatus.BAD_REQUEST


class RetrieveApiResource(BaseApiResource, Resource):
    """
    Retrieve a model instance.
    """
    method_decorators = []

    def __init__(self, decorators):
        self.method_decorators = decorators

    def get(self):
        try:
            if not self.resultset:
                return jsonify({'error': 'Record not found'}), HTTPStatus.NOT_FOUND
            return self.serializer.dump(self.resultset), HTTPStatus.OK
        except ValidationError as e:
            return jsonify({'error': e.messages}), HTTPStatus.BAD_REQUEST


class UpdateApiResource(BaseApiResource, Resource):
    """
    Update a model instance.
    """
    def __init__(self, decorators):
        self.method_decorators = decorators

    def put(self):
        try:
            if not self.resultset:
                return jsonify({'error': 'Record not found'}), HTTPStatus.NOT_FOUND

            data = self.request.get_json()
            result = self.serializer.load(data)
            for key, value in result.items():
                setattr(self.resultset, key, value)
            self.db.session.commit()
            return self.serializer.dump(self.resultset), HTTPStatus.OK

        except ValidationError as e:
            self.db.session.rollback()
            return jsonify({'error': e.messages}), HTTPStatus.BAD_REQUEST

        except Exception as e:
            self.db.session.rollback()
            return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

    def patch(self):
        try:
            if not self.resultset:
                return jsonify({'error': 'Record not found'}), HTTPStatus.NOT_FOUND

            data = self.request.get_json()
            result = self.serializer.load(data, partial=True)
            for key, value in result.items():
                setattr(self.resultset, key, value)
            self.db.session.commit()
            return self.serializer.dump(self.resultset), HTTPStatus.OK

        except ValidationError as e:
            self.db.session.rollback()
            return jsonify({'error': e.messages}), HTTPStatus.BAD_REQUEST

        except Exception as e:
            self.db.session.rollback()
            return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


class DestroyApiResource(BaseApiResource, Resource):
    """
    Destroy a model instance.
    """
    def __init__(self, decorators):
        self.method_decorators = decorators

    def delete(self):
        if not self.resultset:
            return jsonify({'error': 'Record not found'}), HTTPStatus.NOT_FOUND
        try:
            self.db.session.delete(self.resultset)
            self.db.session.commit()
            return jsonify({'message': 'Record successfully deleted'}), HTTPStatus.OK
        except Exception as e:
            self.db.session.rollback()
            return jsonify({'message': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
