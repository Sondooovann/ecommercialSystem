export interface Address {
  id: number;
  recipient_name: string;
  phone: string;
  province: string;
  district: string;
  ward: string;
  street_address: string;
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AddressListResponse {
  addresses: Address[];
}

