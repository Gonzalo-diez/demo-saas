export type MapFilters = {
  salesRepId?: number;
  search?: string;
  isActive?: boolean;
};

export type MapClient = {
  client_id: number;
  client_name: string;
  client_type: string;
  sales_rep_id?: number | null;
  sales_rep_name?: string | null;

  branch_id: number;
  branch_name: string;
  branch_address?: string | null;
  branch_city?: string | null;
  branch_is_main: boolean;

  lat: number;
  lng: number;
  h3_index?: string | null;
  is_active: boolean;
};