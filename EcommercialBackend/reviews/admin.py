# reviews/admin.py
from django.contrib import admin
from .models import Review, OrderReview, ReviewLike, ForbiddenWord

# Đăng ký các model hiện có
admin.site.register(Review)
admin.site.register(OrderReview)
admin.site.register(ReviewLike)

# Đăng ký ForbiddenWord với tùy chỉnh
@admin.register(ForbiddenWord)
class ForbiddenWordAdmin(admin.ModelAdmin):
    list_display = ('word', 'created_at')
    search_fields = ('word',)