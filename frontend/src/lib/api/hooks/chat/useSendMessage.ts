import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../client';
import type { ChatMessage } from '@/types';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Optimistic messages are marked with this prefix in metadata
const OPTIMISTIC_FLAG = '__isOptimistic__';

interface MutationContext {
  previousMessages?: ChatMessage[] | undefined;
  tempId?: string;
}

export interface UseSendMessageOptions {
  sessionId: string;
  onSuccess?: (message: ChatMessage) => void;
  onError?: (error: Error, variables: { content: string }) => void;
}

export function useSendMessage(options: UseSendMessageOptions) {
  const { sessionId, onSuccess, onError } = options;
  const queryClient = useQueryClient();
  
  const mutation = useMutation<ChatMessage, Error, { content: string; tempId?: string }, MutationContext>({
    mutationFn: async ({ content }) => {
      const message = await api.sessions.send(sessionId, content, 'user');
      return message as unknown as ChatMessage;
    },
    onMutate: async ({ content, tempId }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['sessions', sessionId, 'messages'] });
      
      // Snapshot the previous value
      const previousMessages = queryClient.getQueryData<ChatMessage[]>([
        'sessions', sessionId, 'messages', { limit: 100, offset: 0 }
      ]);
      
      // Generate temp ID if not provided
      const messageTempId = tempId || generateId();
      
      // Create optimistic message with metadata flag
      const optimisticMessage: ChatMessage = {
        id: messageTempId,
        session_id: sessionId,
        role: 'user',
        content,
        agent_type: null,
        metadata: { [OPTIMISTIC_FLAG]: true },
        created_at: new Date().toISOString(),
      };
      
      // Optimistically update the cache
      queryClient.setQueryData<ChatMessage[]>(
        ['sessions', sessionId, 'messages', { limit: 100, offset: 0 }],
        (old = []) => [...old, optimisticMessage]
      );
      
      // Return tempId in context so onSuccess can identify this optimistic
      return { previousMessages, tempId: messageTempId };
    },
    onError: (error, variables, context) => {
      // Rollback on error - remove ONLY the failed optimistic message
      if (context?.tempId) {
        queryClient.setQueryData<ChatMessage[]>(
          ['sessions', sessionId, 'messages', { limit: 100, offset: 0 }],
          (old = []) => old.filter(msg => msg.id !== context.tempId)
        );
      } else if (context?.previousMessages) {
        // Fallback: restore previous messages
        queryClient.setQueryData(
          ['sessions', sessionId, 'messages', { limit: 100, offset: 0 }],
          context.previousMessages
        );
      }
      onError?.(error, variables);
    },
    onSuccess: (data, variables, context) => {
      if (!context?.tempId) return;
      
      // Replace the exact optimistic message with the real one
      queryClient.setQueryData<ChatMessage[]>(
        ['sessions', sessionId, 'messages', { limit: 100, offset: 0 }],
        (old = []) => {
          // Remove optimistic by tempId, add real server message
          const filtered = old.filter(msg => 
            msg.id !== context.tempId && 
            msg.metadata?.[OPTIMISTIC_FLAG] !== true
          );
          return [...filtered, data];
        }
      );
      onSuccess?.(data);
    },
    onSettled: () => {
      // Always refetch after error or success to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['sessions', sessionId, 'messages'] });
    },
  });
  
  const sendMessage = (content: string): string => {
    const tempId = generateId();
    mutation.mutate({ content, tempId });
    return tempId;
  };
  
  const sendMessageAsync = async (content: string): Promise<ChatMessage> => {
    return mutation.mutateAsync({ content });
  };

  return {
    sendMessage,
    sendMessageAsync,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    reset: mutation.reset,
  };
}
