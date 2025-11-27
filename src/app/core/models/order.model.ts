export interface OrderAttribute {
  name: string;
  display_name: string;
  value: string;
  display_value: string;
}

export interface OrderVariantDetails {
  id: number;
  sku: string;
  attributes: OrderAttribute[];
}

export interface OrderShopDetails {
  id: number;
  name: string;
  logo: string;
}

export interface OrderItem {
  id: number;
  product_name: string;
  product_image: string;
  variant_details: OrderVariantDetails;
  shop_details: OrderShopDetails;
  quantity: number;
  price: string;
  subtotal: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface OrderTrackingHistory {
  id: number;
  status: string;
  note: string;
  created_by_name: string;
  created_at: string;
}

export interface OrderCustomer {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  avatar: string | null;
}

export interface OrderFirstProduct {
  name: string;
  image: string;
  quantity: number;
  more_items: boolean;
}

// Order summary for list view
export interface OrderSummary {
  id: number;
  total_amount: string;
  payment_method: string;
  payment_status: string;
  customer: OrderCustomer;
  order_status: string;
  items_count: number;
  first_product: OrderFirstProduct;
  created_at: string;
}

// Full order details
export interface Order {
  id: number;
  user: number;
  address: {
    id: number;
    recipient_name: string;
    phone: string;
    province: string;
    district: string;
    ward: string;
    street_address: string;
    is_default: boolean;
  };
  total_amount: string;
  shipping_fee: string;
  discount_amount: string;
  payment_method: string;
  payment_status: string;
  order_status: string;
  notes: string;
  items: OrderItem[];
  tracking_history: OrderTrackingHistory[];
  created_at: string;
  updated_at: string;
}

export interface CreateOrderRequest {
  address_id: number;
  payment_method: 'cod' | 'online';
  notes: string;
  cart_item_ids: number[];
}

export interface CreateOrderResponse extends Order {
  // Response trả về trực tiếp là Order object
}

