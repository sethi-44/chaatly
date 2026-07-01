import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { supabase } from '../supabaseClient';
import { API_URL } from '../constants';

export const MeetupsContext = createContext<any>(null);

export function MeetupsProvider({ children }: { children: React.ReactNode }) {
  const [meetups, setMeetups] = useState<any[]>([]);
  const [hasMoreMeetups, setHasMoreMeetups] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [joinedMeetupIds, setJoinedMeetupIds] = useState<number[]>([]);
  
  const [token, setToken] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  const fetchMeetups = useCallback(async (refresh = false) => {
    try {
      const skip = refresh ? 0 : meetups.length;
      if (refresh) setHasMoreMeetups(true);
      const res = await axios.get(`${API_URL}/meetups?skip=${skip}&limit=20`);
      
      if (res.data.length < 20) {
        setHasMoreMeetups(false);
      }
      
      setMeetups(prev => {
        if (refresh) return res.data;
        const existingIds = new Set(prev.map(m => m.id));
        const newMeetups = res.data.filter((m: any) => !existingIds.has(m.id));
        return [...prev, ...newMeetups];
      });
    } catch (err) {
      console.warn('Failed to fetch meetups context:', err);
    }
  }, [meetups.length]);

  const loadMoreMeetups = useCallback(async () => {
    if (loadingMore || !hasMoreMeetups) return;
    setLoadingMore(true);
    await fetchMeetups(false);
    setLoadingMore(false);
  }, [loadingMore, hasMoreMeetups, fetchMeetups]);

  const fetchJoined = useCallback(async () => {
    if (!token) {
      setJoinedMeetupIds([]);
      return;
    }
    try {
      const res = await axios.get(`${API_URL}/meetups/joined`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setJoinedMeetupIds(res.data);
    } catch (err) {
      console.warn('Failed to fetch joined meetups context:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchMeetups(true);
  }, []);

  useEffect(() => {
    fetchJoined();
  }, [fetchJoined]);

  // Helpers for optimistic UI / realtime
  const addMeetup = useCallback((meetup: any) => {
    setMeetups(prev => {
      if (prev.some(m => m.id === meetup.id)) return prev;
      return [meetup, ...prev];
    });
  }, []);

  const updateMeetup = useCallback((id: number, data: any) => {
    setMeetups(prev => prev.map(m => m.id === id ? { ...m, ...data } : m));
  }, []);

  const removeMeetup = useCallback((id: number) => {
    setMeetups(prev => prev.filter(m => m.id !== id));
    setJoinedMeetupIds(prev => prev.filter(jid => jid !== id));
  }, []);

  const addParticipant = useCallback((meetupId: number, userId: string) => {
    setMeetups(prev => prev.map(m => {
      if (m.id === meetupId) {
        return {
          ...m,
          attendee_count: m.attendee_count + 1,
          spots_left: Math.max(0, (m.spots_left || 0) - 1)
        };
      }
      return m;
    }));
    if (currentUserId && userId === currentUserId) {
      setJoinedMeetupIds(prev => prev.includes(meetupId) ? prev : [...prev, meetupId]);
    }
  }, [currentUserId]);

  const removeParticipant = useCallback((meetupId: number, userId: string) => {
    setMeetups(prev => prev.map(m => {
      if (m.id === meetupId) {
        return {
          ...m,
          attendee_count: Math.max(0, m.attendee_count - 1),
          spots_left: (m.spots_left || 0) + 1
        };
      }
      return m;
    }));
    if (currentUserId && userId === currentUserId) {
      setJoinedMeetupIds(prev => prev.filter(jid => jid !== meetupId));
    }
  }, [currentUserId]);
  const addPhoto = useCallback((meetupId: number, photo: any) => {
    setMeetups(prev => prev.map(m => {
      if (m.id === meetupId) {
        const photos = m.photos || [];
        if (photos.some((p: any) => p.id === photo.id)) return m;
        return { ...m, photos: [...photos, photo] };
      }
      return m;
    }));
  }, []);

  const removePhoto = useCallback((photoId: number) => {
    setMeetups(prev => prev.map(m => {
      const photos = m.photos || [];
      if (photos.some((p: any) => p.id === photoId)) {
        return { ...m, photos: photos.filter((p: any) => p.id !== photoId) };
      }
      return m;
    }));
  }, []);

  // Realtime
  useEffect(() => {
    const channel = supabase.channel('public:meetups_and_participants')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'meetups' }, async (payload) => {
        if (payload.eventType === 'INSERT') {
          // Fetch full meetup to get relations (like host user object)
          try {
            const res = await axios.get(`${API_URL}/meetups/${payload.new.id}`);
            addMeetup(res.data);
          } catch (e) { console.error(e); }
        } else if (payload.eventType === 'UPDATE') {
          updateMeetup(payload.new.id, payload.new);
        } else if (payload.eventType === 'DELETE') {
          removeMeetup(payload.old.id);
        }
      })
      .on('postgres_changes', { event: '*', schema: 'public', table: 'meetup_participants' }, (payload) => {
        if (payload.eventType === 'INSERT') {
          addParticipant(payload.new.meetup_id, payload.new.user_id);
        } else if (payload.eventType === 'DELETE') {
          removeParticipant(payload.old.meetup_id, payload.old.user_id);
        }
      })
      .on('postgres_changes', { event: '*', schema: 'public', table: 'meetup_photos' }, (payload) => {
        if (payload.eventType === 'INSERT') {
          addPhoto(payload.new.meetup_id, payload.new);
        } else if (payload.eventType === 'DELETE') {
          removePhoto(payload.old.id);
        }
      })
      .subscribe((status, err) => {
        console.log('Meetups Realtime Status:', status);
        if (err) console.error('Meetups Realtime Error:', err);
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, [addMeetup, updateMeetup, removeMeetup, addParticipant, removeParticipant, addPhoto, removePhoto]);

  return (
    <MeetupsContext.Provider value={{
      meetups,
      joinedMeetupIds,
      setToken,
      setCurrentUserId,
      refreshMeetups: () => { fetchMeetups(true); fetchJoined(); },
      loadMoreMeetups,
      hasMoreMeetups,
      loadingMore,
      addMeetup, updateMeetup, removeMeetup, addParticipant, removeParticipant,
      addPhoto, removePhoto
    }}>
      {children}
    </MeetupsContext.Provider>
  );
}

export const useMeetups = () => useContext(MeetupsContext);
