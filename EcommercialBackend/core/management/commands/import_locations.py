# core/management/commands/import_locations.py
import json
from django.core.management.base import BaseCommand
from core.models import Province, District, Ward


class Command(BaseCommand):
    help = 'Import dữ liệu địa giới hành chính Việt Nam'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Đường dẫn đến file JSON chứa dữ liệu')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Xóa dữ liệu cũ
            self.stdout.write("Đang xóa dữ liệu cũ...")
            Ward.objects.all().delete()
            District.objects.all().delete()
            Province.objects.all().delete()

            # Import dữ liệu mới
            self.stdout.write("Đang import dữ liệu mới...")
            province_count = 0
            district_count = 0
            ward_count = 0

            for province_data in data:
                # Tạo tỉnh/thành phố
                province_name = province_data['name']
                # Tạo mã code từ tên tỉnh (có thể tùy chỉnh logic này)
                province_code = str(province_count + 1).zfill(2)

                province = Province.objects.create(
                    name=province_name,
                    code=province_code
                )
                province_count += 1

                for district_data in province_data.get('districts', []):
                    # Tạo quận/huyện
                    district_name = district_data['name']
                    # Tạo mã code từ tỉnh và số thứ tự (có thể tùy chỉnh logic này)
                    district_code = f"{province_code}{str(district_count % 1000 + 1).zfill(3)}"

                    district = District.objects.create(
                        province=province,
                        name=district_name,
                        code=district_code
                    )
                    district_count += 1

                    for ward_data in district_data.get('wards', []):
                        # Tạo phường/xã
                        ward_name = ward_data['name']
                        # Tạo mã code từ quận và số thứ tự (có thể tùy chỉnh logic này)
                        ward_code = f"{district_code}{str(ward_count % 1000 + 1).zfill(3)}"

                        Ward.objects.create(
                            district=district,
                            name=ward_name,
                            code=ward_code
                        )
                        ward_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'Import dữ liệu thành công! Đã thêm {province_count} tỉnh/thành phố, '
                f'{district_count} quận/huyện và {ward_count} phường/xã.'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Lỗi khi import dữ liệu: {str(e)}'))