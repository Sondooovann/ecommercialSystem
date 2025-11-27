export interface Product {
  id: number;
  shop: number;
  shop_name: string;
  category: number;
  category_name: string;
  name: string;
  slug: string;
  description: string;
  short_description: string;
  price: string;
  sale_price: string;
  stock: number;
  product_type: string;
  status: string;
  featured: boolean;
  rating: string;
  view_count: number;
  sold_count: number;
  thumbnail: string;
  created_at: string;
  updated_at: string;
  total_sold: number;
}

export interface ProductListResponse {
  products: Product[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

export interface ProductApiResponse {
  status: string;
  message: string;
  data: ProductListResponse;
}

export interface ProductDetailResponse {
  success: boolean;
  message: string;
  data: {
    status: string;
    message: string;
    data: ProductDetail;
  };
}

export interface ProductDetail {
  id: number;
  shop: ShopInfo;
  category: CategoryInfo;
  name: string;
  slug: string;
  description: string;
  short_description: string;
  price: string;
  sale_price: string;
  stock: number;
  product_type: string;
  status: string;
  featured: boolean;
  rating: string;
  view_count: number;
  sold_count: number;
  images: ProductImage[];
  variants: ProductVariant[];
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ShopInfo {
  id: number;
  name: string;
  logo: string;
  banner: string;
  status: string;
  rating: string;
  created_at: string;
}

export interface CategoryInfo {
  id: number;
  name: string;
  image: string | null;
  status: string;
}

export interface ProductImage {
  id: number;
  image_url: string;
  is_thumbnail: boolean;
  display_order: number;
  created_at: string;
}

export interface ProductVariant {
  id: number;
  product: number;
  sku: string;
  price: string;
  sale_price: string;
  stock: number;
  image_url: string | null;
  attribute_values: VariantAttributeValue[];
  created_at: string;
  updated_at: string;
}

export interface VariantAttributeValue {
  id: number;
  value: string;
  display_value: string;
  attribute: ProductAttribute;
}

export interface ProductAttribute {
  id: number;
  name: string;
  display_name: string;
  attribute_type: string;
}


