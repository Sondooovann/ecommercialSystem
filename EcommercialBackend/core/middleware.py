from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse


class CustomResponseMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Chỉ sửa đổi các phản hồi API
        if request.path.startswith('/api/'):
            # Nếu phản hồi đã có cấu trúc tùy chỉnh, trả về nó
            try:
                if hasattr(response, 'data') and ('success' in response.data):
                    return response
            except:
                pass

            # Định dạng phản hồi
            status_code = response.status_code

            if 200 <= status_code < 300:
                data = {
                    'success': True,
                    'data': response.data if hasattr(response, 'data') else None,
                    'message': 'Thành công'
                }
            else:
                data = {
                    'success': False,
                    'errors': response.data if hasattr(response, 'data') else None,
                    'message': 'Lỗi'
                }

            # Tạo JsonResponse mới
            new_response = JsonResponse(data, status=status_code)
            return new_response

        return response