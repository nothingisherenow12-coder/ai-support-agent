export type ActionType = 'create_ticket';

export type ActionStatus = 'proposed' | 'approved' | 'rejected' | 'executed';

export interface ActionProposal {
  action_type: ActionType;
  customer_id: number | null;
  title: string;
  description: string;
  reason: string;
  requires_approval: boolean;
}

// Persisted action record from the backend actions API.
export interface ActionRecord extends ActionProposal {
  id: number;
  status: ActionStatus;
  created_at: string;
  updated_at: string;
}

export interface ExecuteActionResult {
  action_id: number;
  action_status: ActionStatus;
  ticket: {
    id: number;
    customer_id: number;
    title: string;
    description: string;
    priority: string;
    status: string;
    created_at: string;
    updated_at: string;
  };
}
