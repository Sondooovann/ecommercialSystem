from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class CustomError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Lỗi xảy ra.'
    default_code = 'custom_error'

    def __init__(self, detail=None, code=None, status_code=None):
        super().__init__(detail, code)
        if status_code:
            self.status_code = status_code


def custom_exception_handler(exc, context):
    # Gọi exception handler mặc định của REST framework
    response = exception_handler(exc, context)

    # Thêm định dạng phản hồi tùy chỉnh
    if response is not None:
        response.data = {
            'success': False,
            'message': 'Lỗi',
            'errors': response.data
        }

    return response