export interface Customer {
  id: number;
  name: string;
  email: string;
  company: string | null;
}

export interface Ticket {
  id: number;
  customer_id: number;
  title: string;
  description: string;
  external_id?: string | null;
  priority: string;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
}
