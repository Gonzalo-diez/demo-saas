export type ClientLoginInput = {
  email: string;
  password: string;
};

// Espejo de ClientResponse del backend (app/schemas/client_schema.py)
export type ClientUser = {
  id: number;
  name: string;
  client_type: string;
  tax_id: string | null;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  current_balance: number;
  created_at: string;
  updated_at: string;
};

export type MessageResponse = {
  message: string;
};