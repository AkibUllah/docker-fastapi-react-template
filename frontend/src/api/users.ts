import { api } from "@/api/client";
import type { Page, User } from "@/types";

export interface UserUpdateInput {
  email?: string;
  full_name?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export const usersApi = {
  async list(offset = 0, limit = 20): Promise<Page<User>> {
    const { data } = await api.get<Page<User>>("/users", { params: { offset, limit } });
    return data;
  },
  async update(id: string, input: UserUpdateInput): Promise<User> {
    const { data } = await api.patch<User>(`/users/${id}`, input);
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/users/${id}`);
  },
};
