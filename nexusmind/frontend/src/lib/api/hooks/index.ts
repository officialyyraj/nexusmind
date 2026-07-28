import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';

export function useAgents() { 
  return useQuery({ queryKey: ['agents'], queryFn: api.agents.list }); 
}

export function useAgent(id: string) { 
  return useQuery({ queryKey: ['agents', id], queryFn: () => api.agents.get(id), enabled: !!id }); 
}

export function useSessions() { 
  return useQuery({ queryKey: ['sessions'], queryFn: () => api.sessions.list() }); 
}

export function useSession(id: string) { 
  return useQuery({ queryKey: ['sessions', id], queryFn: () => api.sessions.get(id), enabled: !!id }); 
}

export function useSessionMessages(sessionId: string) { 
  return useQuery({ queryKey: ['sessions', sessionId, 'messages'], queryFn: () => api.sessions.messages(sessionId), enabled: !!sessionId }); 
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { title?: string }) => api.sessions.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

export function useUpdateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; status?: string } }) =>
      api.sessions.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['sessions', id] });
    },
  });
}

export function useDeleteSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.sessions.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });
}

// DEFERRED: Projects feature not implemented in Phase 3
// export function useProjects() { 
//   return useQuery({ queryKey: ['projects'], queryFn: api.projects.list }); 
// }

export function usePlugins() { 
  return useQuery({ queryKey: ['plugins'], queryFn: api.plugins.list }); 
}

// DEFERRED: Logs feature not implemented in Phase 3
// export function useLogs(params?: Record<string, string>) { 
//   return useQuery({ queryKey: ['logs', params], queryFn: () => api.logs.list(params) }); 
// }

// DEFERRED: Routing feature not implemented in Phase 3
// export function useModels() { 
//   return useQuery({ queryKey: ['models'], queryFn: api.routing.models }); 
// }
