export enum UserRole {
  CUSTOMER = 'customer',
  SHOP_OWNER = 'shop_owner',
  ADMIN = 'admin'
};
export type UserStatus = 'active' | 'inactive' | 'banned';

export interface User {
  id?: number;
  email: string;
  full_name: string;
  phone?: string | null;
  avatar?: string | null;
  role: UserRole;
  status: UserStatus;
  is_staff?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UserLogin {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

export interface LoginResponse {
  refresh: string;
  access: string;
  user: UserLogin;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserRegistrationRequest {
  email: string;
  full_name: string;
  phone: string;
  password: string;
  confirm_password: string;
  role: 'customer' | 'shop_owner';
}

export interface UserRegistrationResponse {
  email: string;
  role: string;
}


