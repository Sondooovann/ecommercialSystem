export interface Category {
  id: number;
  name: string;
  image: string | null;
  status: string;
  parent: number | null;
  description?: string;
}

export interface CategoryResponse {
  success: boolean;
  data: {
    status: string;
    message: string;
    data: Category[];
  };
  message: string;
}

export interface CategoryCreateRequest {
  name: string;
  description?: string;
  is_active: boolean;
  parent: string | number;
  image?: File | null;
}

export interface CategoryUpdateRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  parent?: string | number;
  image?: File | null;
}

export interface CategoryTreeNode extends Category {
  children?: CategoryTreeNode[];
  level?: number;
}

