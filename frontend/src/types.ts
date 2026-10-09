export interface User {
  id: number;
  email: string;
  role: "citizen" | "officer" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface Complaint {
  complaint_id: string;
  text: string;
  latitude: number;
  longitude: number;
  image_path: string | null;
  status: string;
  is_flagged: boolean;
  flag_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplaintList {
  total: number;
  items: Complaint[];
}

export interface ComplaintSubmission {
  complaint_id: string;
  status: string;
  message: string;
}