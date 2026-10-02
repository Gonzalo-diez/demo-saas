export type MapFilters = {
  lat?: number;
  lng?: number;
  radius_km?: number;
  search?: string;
  isActive?: boolean;
};

export type MapSalesRep = {
  id: number;
  name: string;
  home_lat: number | null;
  home_lng: number | null;
  coverage_radius_km: number | null;
  home_h3_index?: string | null;
};
