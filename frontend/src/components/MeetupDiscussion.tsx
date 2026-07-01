import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Image,
} from 'react-native';
import Animated, {
  FadeInDown,
  FadeIn,
} from 'react-native-reanimated';
import axios from 'axios';
import { API_URL, C } from '../constants';
import { supabase } from '../supabaseClient';

// ── Types ────────────────────────────────────────────────────────────

interface DiscussionAuthor {
  id: string;
  username: string;
  profile_picture_url: string | null;
}

interface DiscussionReply {
  id: number;
  meetup_id: number;
  content: string;
  created_at: string;
  updated_at: string;
  author: DiscussionAuthor;
}

interface DiscussionMessage {
  id: number;
  meetup_id: number;
  content: string;
  created_at: string;
  updated_at: string;
  author: DiscussionAuthor;
  reply_count: number;
  replies: DiscussionReply[];
}

interface PaginationInfo {
  page: number;
  pages: number;
  limit: number;
  total: number;
}

// ── Time Ago Helper ──────────────────────────────────────────────────

function timeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// ── Avatar Component ─────────────────────────────────────────────────

function DiscussionAvatar({ author, size = 36 }: { author: DiscussionAuthor; size?: number }) {
  const initial = author.username?.charAt(0)?.toUpperCase() || '?';
  const borderRadius = size / 2;

  if (author.profile_picture_url?.startsWith('http')) {
    return (
      <Image
        source={{ uri: author.profile_picture_url }}
        style={[dStyles.avatar, { width: size, height: size, borderRadius }]}
      />
    );
  }

  return (
    <View style={[dStyles.avatarFallback, { width: size, height: size, borderRadius }]}>
      <Text style={[dStyles.avatarInitial, { fontSize: size * 0.42 }]}>{initial}</Text>
    </View>
  );
}

// ── Skeleton Loader ──────────────────────────────────────────────────

function DiscussionSkeleton() {
  return (
    <View style={dStyles.skeletonContainer}>
      {[1, 2, 3].map((i) => (
        <View key={i} style={dStyles.skeletonMessage}>
          <View style={dStyles.skeletonRow}>
            <View style={dStyles.skeletonAvatar} />
            <View style={{ flex: 1 }}>
              <View style={dStyles.skeletonLine} />
              <View style={[dStyles.skeletonLine, { width: '70%' }]} />
            </View>
          </View>
        </View>
      ))}
    </View>
  );
}

// ── Main Component ───────────────────────────────────────────────────

export default function MeetupDiscussion({
  meetupId,
  token,
  currentUserId,
  isHost,
  isHostOrParticipant,
}: {
  meetupId: number;
  token: string;
  currentUserId: string;
  isHost: boolean;
  isHostOrParticipant: boolean;
}) {
  // ── Discussion State (Realtime-Ready) ────────────────────────────
  const [messages, setMessages] = useState<DiscussionMessage[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo>({ page: 1, pages: 1, limit: 20, total: 0 });
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');

  // Composer state
  const [newMessage, setNewMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Reply state
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [replySubmitting, setReplySubmitting] = useState(false);

  // Edit state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editSubmitting, setEditSubmitting] = useState(false);

  // Delete state
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Prevent duplicate submissions
  const submitRef = useRef(false);

  // ── Centralized State Helpers (Realtime-Ready) ───────────────────
  // These methods are designed to be called by future Supabase Realtime
  // event handlers: INSERT → addDiscussionMessage/addReply,
  // UPDATE → updateDiscussionMessage, DELETE → removeDiscussionMessage

  const addDiscussionMessage = useCallback((message: DiscussionMessage) => {
    setMessages(prev => {
      // Deduplicate by ID (important for realtime)
      if (prev.some(m => m.id === message.id)) return prev;
      return [...prev, message];
    });
    setPagination(prev => ({ ...prev, total: prev.total + 1 }));
  }, []);

  const updateDiscussionMessage = useCallback((updatedMessage: { id: number; content: string; updated_at: string }) => {
    setMessages(prev =>
      prev.map(m => {
        if (m.id === updatedMessage.id) {
          return { ...m, content: updatedMessage.content, updated_at: updatedMessage.updated_at };
        }
        // Also check replies
        const updatedReplies = m.replies.map(r =>
          r.id === updatedMessage.id
            ? { ...r, content: updatedMessage.content, updated_at: updatedMessage.updated_at }
            : r
        );
        if (updatedReplies !== m.replies) {
          return { ...m, replies: updatedReplies };
        }
        return m;
      })
    );
  }, []);

  const removeDiscussionMessage = useCallback((messageId: number) => {
    setMessages(prev => {
      // Check if it's a top-level message
      const isTopLevel = prev.some(m => m.id === messageId);
      if (isTopLevel) {
        return prev.filter(m => m.id !== messageId);
      }
      // Otherwise it's a reply — remove from parent
      return prev.map(m => ({
        ...m,
        replies: m.replies.filter(r => r.id !== messageId),
        reply_count: m.replies.filter(r => r.id !== messageId).length,
      }));
    });
  }, []);

  const addReply = useCallback((parentId: number, reply: DiscussionReply) => {
    setMessages(prev =>
      prev.map(m => {
        if (m.id === parentId) {
          // Deduplicate
          if (m.replies.some(r => r.id === reply.id)) return m;
          return {
            ...m,
            replies: [...m.replies, reply],
            reply_count: m.reply_count + 1,
          };
        }
        return m;
      })
    );
  }, []);

  // ── Fetch Discussion ─────────────────────────────────────────────

  const fetchDiscussion = useCallback(async (page = 1, append = false, isBackgroundRefresh = false) => {
    try {
      if (!isBackgroundRefresh) {
        if (!append) setLoading(true);
        else setLoadingMore(true);
      }

      const res = await axios.get(`${API_URL}/meetups/${meetupId}/discussion`, {
        params: { page, limit: 20 },
      });

      const data = res.data;
      if (append) {
        setMessages(prev => {
          const existingIds = new Set(prev.map(m => m.id));
          const newMessages = data.messages.filter((m: DiscussionMessage) => !existingIds.has(m.id));
          return [...prev, ...newMessages];
        });
      } else {
        setMessages(data.messages);
      }
      setPagination({ page: data.page, pages: data.pages, limit: data.limit, total: data.total });
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to load discussion'));
      setTimeout(() => setError(''), 5000);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [meetupId]);

  useEffect(() => {
    fetchDiscussion();
  }, [fetchDiscussion]);

  // ── Realtime Subscription ────────────────────────────────────────

  useEffect(() => {
    const channel = supabase
      .channel(`public:discussion_messages:meetup_id=eq.${meetupId}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'discussion_messages', filter: `meetup_id=eq.${meetupId}` },
        (payload) => {
          console.log('REALTIME PAYLOAD:', payload);
          if (payload.eventType === 'UPDATE') {
            updateDiscussionMessage({
              id: payload.new.id,
              content: payload.new.content,
              updated_at: payload.new.updated_at,
            });
          } else if (payload.eventType === 'DELETE') {
            removeDiscussionMessage(payload.old.id);
          } else if (payload.eventType === 'INSERT') {
            // Re-fetch to get the full message with author details.
            // We use fetchDiscussion with isBackgroundRefresh=true to avoid the loading skeleton flash.
            fetchDiscussion(1, false, true);
          }
        }
      )
      .subscribe((status, err) => {
        console.log('Supabase Realtime Status:', status);
        if (err) console.error('Supabase Realtime Error:', err);
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, [meetupId, currentUserId, updateDiscussionMessage, removeDiscussionMessage, fetchDiscussion]);

  // ── Create Message ───────────────────────────────────────────────

  const handleCreateMessage = async () => {
    const trimmed = newMessage.trim();
    if (!trimmed || submitRef.current) return;
    submitRef.current = true;
    setSubmitting(true);
    setError('');

    try {
      const res = await axios.post(
        `${API_URL}/meetups/${meetupId}/discussion`,
        { content: trimmed },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Optimistic: add to local state
      addDiscussionMessage(res.data);
      setNewMessage('');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to send message'));
      setTimeout(() => setError(''), 5000);
    } finally {
      setSubmitting(false);
      submitRef.current = false;
    }
  };

  // ── Reply ────────────────────────────────────────────────────────

  const handleReply = async (parentId: number) => {
    const trimmed = replyContent.trim();
    if (!trimmed || replySubmitting) return;
    setReplySubmitting(true);
    setError('');

    try {
      const res = await axios.post(
        `${API_URL}/discussion/${parentId}/reply`,
        { content: trimmed },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      addReply(parentId, res.data);
      setReplyContent('');
      setReplyingTo(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to send reply'));
      setTimeout(() => setError(''), 5000);
    } finally {
      setReplySubmitting(false);
    }
  };

  // ── Edit ─────────────────────────────────────────────────────────

  const startEditing = (id: number, content: string) => {
    setEditingId(id);
    setEditContent(content);
    // Close reply box if open
    setReplyingTo(null);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditContent('');
  };

  const handleEdit = async () => {
    const trimmed = editContent.trim();
    if (!trimmed || !editingId || editSubmitting) return;
    setEditSubmitting(true);
    setError('');

    try {
      const res = await axios.put(
        `${API_URL}/discussion/${editingId}`,
        { content: trimmed },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      updateDiscussionMessage({
        id: editingId,
        content: res.data.content,
        updated_at: res.data.updated_at,
      });
      cancelEditing();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to edit message'));
      setTimeout(() => setError(''), 5000);
    } finally {
      setEditSubmitting(false);
    }
  };

  // ── Delete ───────────────────────────────────────────────────────

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    setError('');

    try {
      await axios.delete(`${API_URL}/discussion/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      removeDiscussionMessage(id);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0].msg : (detail || 'Failed to delete message'));
      setTimeout(() => setError(''), 5000);
    } finally {
      setDeletingId(null);
    }
  };

  // ── Load More ────────────────────────────────────────────────────

  const handleLoadMore = () => {
    if (pagination.page < pagination.pages && !loadingMore) {
      fetchDiscussion(pagination.page + 1, true);
    }
  };

  // ── Can user perform action? ─────────────────────────────────────

  const canEdit = (authorId: string) => currentUserId === authorId;
  const canDelete = (authorId: string) => currentUserId === authorId || isHost;
  const isEdited = (msg: { created_at: string; updated_at: string }) => msg.updated_at !== msg.created_at;

  // ── Render Reply ─────────────────────────────────────────────────

  const renderReply = (reply: DiscussionReply) => {
    const isEditingThis = editingId === reply.id;

    return (
      <Animated.View key={reply.id} entering={FadeIn.duration(300)} style={dStyles.replyContainer}>
        <View style={dStyles.replyIndent}>
          <Text style={dStyles.replyConnector}>↳</Text>
        </View>
        <View style={dStyles.replyContent}>
          <View style={dStyles.messageHeader}>
            <DiscussionAvatar author={reply.author} size={28} />
            <View style={dStyles.messageHeaderText}>
              <Text style={dStyles.authorName}>{reply.author.username}</Text>
              <View style={dStyles.timeBadge}>
                <Text style={dStyles.timeText}>
                  {timeAgo(reply.created_at)}
                  {isEdited(reply) ? ' · edited' : ''}
                </Text>
              </View>
            </View>
            {/* Actions menu */}
            {(canEdit(reply.author.id) || canDelete(reply.author.id)) && (
              <View style={dStyles.actionsRow}>
                {canEdit(reply.author.id) && (
                  <TouchableOpacity
                    onPress={() => startEditing(reply.id, reply.content)}
                    style={dStyles.actionBtn}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    <Text style={dStyles.actionText}>✏️</Text>
                  </TouchableOpacity>
                )}
                {canDelete(reply.author.id) && (
                  <TouchableOpacity
                    onPress={() => handleDelete(reply.id)}
                    style={dStyles.actionBtn}
                    disabled={deletingId === reply.id}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    {deletingId === reply.id ? (
                      <ActivityIndicator size="small" color={C.textMuted} />
                    ) : (
                      <Text style={dStyles.actionText}>🗑️</Text>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>
          {isEditingThis ? (
            <View style={dStyles.editBox}>
              <TextInput
                style={dStyles.editInput}
                value={editContent}
                onChangeText={setEditContent}
                multiline
                maxLength={500}
                placeholderTextColor={C.textMuted}
              />
              <View style={dStyles.editActions}>
                <TouchableOpacity onPress={cancelEditing} style={dStyles.editCancelBtn}>
                  <Text style={dStyles.editCancelText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={handleEdit}
                  style={[dStyles.editSaveBtn, (!editContent.trim()) && { opacity: 0.5 }]}
                  disabled={!editContent.trim() || editSubmitting}
                >
                  {editSubmitting ? (
                    <ActivityIndicator size="small" color={C.surface} />
                  ) : (
                    <Text style={dStyles.editSaveText}>Save</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <Text style={dStyles.messageContent}>{reply.content}</Text>
          )}
        </View>
      </Animated.View>
    );
  };

  // ── Render Message ───────────────────────────────────────────────

  const renderMessage = (message: DiscussionMessage) => {
    const isEditingThis = editingId === message.id;
    const isReplyingToThis = replyingTo === message.id;

    return (
      <Animated.View key={message.id} entering={FadeInDown.duration(400)} style={dStyles.messageContainer}>
        {/* Top-level message */}
        <View style={dStyles.messageInner}>
          <View style={dStyles.messageHeader}>
            <DiscussionAvatar author={message.author} size={36} />
            <View style={dStyles.messageHeaderText}>
              <Text style={dStyles.authorName}>{message.author.username}</Text>
              <View style={dStyles.timeBadge}>
                <Text style={dStyles.timeText}>
                  {timeAgo(message.created_at)}
                  {isEdited(message) ? ' · edited' : ''}
                </Text>
              </View>
            </View>
            {/* Actions */}
            {(canEdit(message.author.id) || canDelete(message.author.id)) && (
              <View style={dStyles.actionsRow}>
                {canEdit(message.author.id) && (
                  <TouchableOpacity
                    onPress={() => startEditing(message.id, message.content)}
                    style={dStyles.actionBtn}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    <Text style={dStyles.actionText}>✏️</Text>
                  </TouchableOpacity>
                )}
                {canDelete(message.author.id) && (
                  <TouchableOpacity
                    onPress={() => handleDelete(message.id)}
                    style={dStyles.actionBtn}
                    disabled={deletingId === message.id}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    {deletingId === message.id ? (
                      <ActivityIndicator size="small" color={C.textMuted} />
                    ) : (
                      <Text style={dStyles.actionText}>🗑️</Text>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>

          {isEditingThis ? (
            <View style={dStyles.editBox}>
              <TextInput
                style={dStyles.editInput}
                value={editContent}
                onChangeText={setEditContent}
                multiline
                maxLength={500}
                placeholderTextColor={C.textMuted}
              />
              <View style={dStyles.editActions}>
                <TouchableOpacity onPress={cancelEditing} style={dStyles.editCancelBtn}>
                  <Text style={dStyles.editCancelText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={handleEdit}
                  style={[dStyles.editSaveBtn, (!editContent.trim()) && { opacity: 0.5 }]}
                  disabled={!editContent.trim() || editSubmitting}
                >
                  {editSubmitting ? (
                    <ActivityIndicator size="small" color={C.surface} />
                  ) : (
                    <Text style={dStyles.editSaveText}>Save</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <Text style={dStyles.messageContent}>{message.content}</Text>
          )}

          {/* Reply button */}
          {isHostOrParticipant && !isEditingThis && (
            <TouchableOpacity
              onPress={() => {
                setReplyingTo(isReplyingToThis ? null : message.id);
                setReplyContent('');
                setEditingId(null);
              }}
              style={dStyles.replyBtn}
              hitSlop={{ top: 4, bottom: 4, left: 8, right: 8 }}
            >
              <Text style={dStyles.replyBtnText}>
                {isReplyingToThis ? 'Cancel' : 'Reply'}
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Replies */}
        {message.replies.length > 0 && (
          <View style={dStyles.repliesList}>
            {message.replies.map(renderReply)}
          </View>
        )}

        {/* Reply composer */}
        {isReplyingToThis && (
          <Animated.View entering={FadeIn.duration(200)} style={dStyles.replyComposer}>
            <View style={dStyles.replyComposerInner}>
              <TextInput
                style={dStyles.replyInput}
                placeholder="Write a reply..."
                placeholderTextColor={C.textMuted}
                value={replyContent}
                onChangeText={setReplyContent}
                multiline
                maxLength={500}
                autoFocus
              />
              <TouchableOpacity
                onPress={() => handleReply(message.id)}
                style={[dStyles.replySendBtn, (!replyContent.trim()) && { opacity: 0.4 }]}
                disabled={!replyContent.trim() || replySubmitting}
              >
                {replySubmitting ? (
                  <ActivityIndicator size="small" color={C.surface} />
                ) : (
                  <Text style={dStyles.replySendText}>↑</Text>
                )}
              </TouchableOpacity>
            </View>
          </Animated.View>
        )}
      </Animated.View>
    );
  };

  // ── Main Render ──────────────────────────────────────────────────

  return (
    <View style={dStyles.container}>
      {/* Section Header */}
      <View style={dStyles.sectionHeader}>
        <Text style={dStyles.sectionTitle}>Discussion</Text>
        {pagination.total > 0 && (
          <View style={dStyles.countBadge}>
            <Text style={dStyles.countBadgeText}>{pagination.total}</Text>
          </View>
        )}
      </View>

      {/* Error */}
      {error ? (
        <Animated.View entering={FadeIn} style={dStyles.errorBanner}>
          <Text style={dStyles.errorText}>{error}</Text>
        </Animated.View>
      ) : null}

      {/* Loading */}
      {loading ? (
        <DiscussionSkeleton />
      ) : messages.length === 0 ? (
        /* Empty State */
        <Animated.View entering={FadeIn.duration(400)} style={dStyles.emptyState}>
          <Text style={dStyles.emptyEmoji}>💬</Text>
          <Text style={dStyles.emptyTitle}>No discussion yet.</Text>
          <Text style={dStyles.emptySubtitle}>
            Start the conversation and help everyone{'\n'}prepare for the meetup.
          </Text>
        </Animated.View>
      ) : (
        /* Messages */
        <View style={dStyles.messagesList}>
          {messages.map(renderMessage)}

          {/* Load More */}
          {pagination.page < pagination.pages && (
            <TouchableOpacity
              onPress={handleLoadMore}
              style={dStyles.loadMoreBtn}
              disabled={loadingMore}
            >
              {loadingMore ? (
                <ActivityIndicator size="small" color={C.primary} />
              ) : (
                <Text style={dStyles.loadMoreText}>Load more messages</Text>
              )}
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Composer (only for host/participants) */}
      {isHostOrParticipant && (
        <View style={dStyles.composer}>
          <TextInput
            style={dStyles.composerInput}
            placeholder="Start the discussion..."
            placeholderTextColor={C.textMuted}
            value={newMessage}
            onChangeText={setNewMessage}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            onPress={handleCreateMessage}
            style={[dStyles.composerSendBtn, (!newMessage.trim()) && { opacity: 0.4 }]}
            disabled={!newMessage.trim() || submitting}
          >
            {submitting ? (
              <ActivityIndicator size="small" color={C.surface} />
            ) : (
              <Text style={dStyles.composerSendText}>↑</Text>
            )}
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────

const dStyles = StyleSheet.create({
  container: {
    borderTopWidth: 1,
    borderTopColor: C.border,
    paddingTop: 20,
    marginTop: 8,
  },

  // Section Header
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: C.text,
    letterSpacing: -0.3,
  },
  countBadge: {
    backgroundColor: C.primary + '18',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  countBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: C.primary,
  },

  // Error
  errorBanner: {
    backgroundColor: '#FEF0F3',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1.5,
    borderColor: C.error + '40',
  },
  errorText: {
    color: C.error,
    fontWeight: '600',
    fontSize: 13,
    textAlign: 'center',
  },

  // Empty State
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 16,
  },
  emptyEmoji: {
    fontSize: 40,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
    marginBottom: 6,
  },
  emptySubtitle: {
    fontSize: 14,
    color: C.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },

  // Skeleton
  skeletonContainer: {
    paddingVertical: 8,
  },
  skeletonMessage: {
    marginBottom: 16,
  },
  skeletonRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  skeletonAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: C.border,
  },
  skeletonLine: {
    height: 12,
    backgroundColor: C.border,
    borderRadius: 6,
    marginBottom: 6,
    width: '90%',
  },

  // Message
  messagesList: {
    gap: 0,
  },
  messageContainer: {
    marginBottom: 4,
  },
  messageInner: {
    paddingVertical: 12,
    paddingHorizontal: 0,
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 10,
  },
  messageHeaderText: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  authorName: {
    fontSize: 14,
    fontWeight: '700',
    color: C.text,
  },
  timeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeText: {
    fontSize: 12,
    color: C.textMuted,
    fontWeight: '500',
  },
  messageContent: {
    fontSize: 15,
    color: C.text,
    lineHeight: 22,
    marginLeft: 46,
  },

  // Avatar
  avatar: {
    backgroundColor: C.border,
  },
  avatarFallback: {
    backgroundColor: C.primary + '18',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: {
    fontWeight: '800',
    color: C.primary,
  },

  // Actions
  actionsRow: {
    flexDirection: 'row',
    gap: 4,
  },
  actionBtn: {
    padding: 4,
  },
  actionText: {
    fontSize: 14,
  },

  // Reply button
  replyBtn: {
    marginLeft: 46,
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  replyBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.primary,
  },

  // Replies
  repliesList: {
    marginLeft: 16,
    borderLeftWidth: 2,
    borderLeftColor: C.border,
    paddingLeft: 0,
  },
  replyContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 8,
    paddingLeft: 8,
  },
  replyIndent: {
    width: 20,
    alignItems: 'center',
    paddingTop: 2,
  },
  replyConnector: {
    fontSize: 14,
    color: C.textMuted,
    fontWeight: '600',
  },
  replyContent: {
    flex: 1,
  },

  // Reply composer
  replyComposer: {
    marginLeft: 46,
    marginTop: 4,
    marginBottom: 8,
  },
  replyComposerInner: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: C.inputBg,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: C.border,
    paddingLeft: 12,
    paddingRight: 4,
    paddingVertical: 4,
  },
  replyInput: {
    flex: 1,
    fontSize: 14,
    color: C.text,
    minHeight: 36,
    maxHeight: 80,
    paddingVertical: 8,
  },
  replySendBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: C.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  replySendText: {
    fontSize: 16,
    fontWeight: '800',
    color: C.surface,
  },

  // Edit
  editBox: {
    marginLeft: 46,
    marginTop: 4,
  },
  editInput: {
    backgroundColor: C.inputBg,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: C.primary + '60',
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: C.text,
    minHeight: 40,
    maxHeight: 100,
  },
  editActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    gap: 8,
  },
  editCancelBtn: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 999,
    backgroundColor: C.inputBg,
    borderWidth: 1,
    borderColor: C.border,
  },
  editCancelText: {
    fontSize: 13,
    fontWeight: '600',
    color: C.textSecondary,
  },
  editSaveBtn: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 999,
    backgroundColor: C.primary,
  },
  editSaveText: {
    fontSize: 13,
    fontWeight: '700',
    color: C.surface,
  },

  // Composer
  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: C.inputBg,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: C.border,
    paddingLeft: 14,
    paddingRight: 4,
    paddingVertical: 4,
    marginTop: 12,
  },
  composerInput: {
    flex: 1,
    fontSize: 15,
    color: C.text,
    minHeight: 40,
    maxHeight: 100,
    paddingVertical: 10,
  },
  composerSendBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: C.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  composerSendText: {
    fontSize: 18,
    fontWeight: '800',
    color: C.surface,
  },

  // Load More
  loadMoreBtn: {
    alignItems: 'center',
    paddingVertical: 12,
    marginTop: 4,
  },
  loadMoreText: {
    fontSize: 14,
    fontWeight: '600',
    color: C.primary,
  },
});
