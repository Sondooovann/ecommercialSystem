export interface VariantAttribute {
  name: string;
  display_name: string;
  value: string;
  display_value: string;
}

export interface VariantDetails {
  id: number;
  product_id: number;
  product_slug: string;
  product_name: string;
  sku: string;
  image_url: string;
  attributes: VariantAttribute[];
  stock: number;
  shop_id: number;
  shop_name: string;
}

export interface CartItem {
  id?: number;
  variant: number;
  variant_details: VariantDetails;
  quantity: number;
  price: string;
  total_price: string;
  created_at: string;
}

export interface Cart {
  id: number;
  user: number;
  items: CartItem[];
  total_items: number;
  total_price: string;
  created_at: string;
  updated_at: string;
}

export interface CartResponse {
  success: boolean;
  data: {
    status: string;
    message: string;
    data: Cart;
  };
  message: string;
}


