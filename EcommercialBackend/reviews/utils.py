# reviews/utils.py
from .models import ForbiddenWord

def check_forbidden_words(text):
    """
    Kiểm tra nếu văn bản chứa từ cấm.
    Trả về tuple (contains_forbidden, word) trong đó:
    - contains_forbidden là boolean chỉ ra nếu tìm thấy từ cấm
    - word là từ cấm đầu tiên tìm thấy, hoặc None nếu không tìm thấy
    """
    if not text:
        return False, None

    # Lấy tất cả từ cấm
    forbidden_words = list(ForbiddenWord.objects.values_list('word', flat=True))

    # Chuyển sang chữ thường để so sánh không phân biệt hoa thường
    text_lower = text.lower()

    # Kiểm tra từng từ cấm
    for word in forbidden_words:
        if word.lower() in text_lower:
            return True, word

    return False, None