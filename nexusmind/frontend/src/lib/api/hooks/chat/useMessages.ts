import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../client';
import type { ChatMessage } from '@/types';

export interface UseMessagesOptions {
  sessionId: string;
  limit?: number;
  offset?: number;
  enabled?: boolean;
}

export function useMessages(options: UseMessagesOptions) {
  const { sessionId, limit = 100, offset = 0, enabled = true } = options;
  
  const queryClient = useQueryClient();
  
  const query = useQuery<ChatMessage[]>({
    queryKey: ['sessions', sessionId, 'messages', { limit, offset }],
    queryFn: async () => {
      const messages = await api.sessions.messages(sessionId, { limit: String(limit), offset: String(offset) });
      return messages as unknown as ChatMessage[];
    },
    enabled: enabled && !!sessionId,
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: false,
  });

  const invalidateMessages = () => {
    queryClient.invalidateQueries({ queryKey: ['sessions', sessionId, 'messages'] });
  };

  const refetch = () => {
    query.refetch();
  };

  return {
    messages: query.data || [],
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    error: query.error,
    isEmpty: !query.isLoading && !query.data?.length,
    invalidateMessages,
    refetch,
  };
}
