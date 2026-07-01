import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Pressable,
  Image,
  ActivityIndicator,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import { SafeAreaView } from "react-native-safe-area-context";
import Animated, {
  FadeInDown,
  FadeInRight,
  FadeIn,
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from "react-native-reanimated";
import { C, SMALL_CARD_W, SHADOW_SM, SHADOW_MD, softBg, CARD_COLORS, CARD_EMOJIS, getCardColor, getCardEmoji } from '../constants';

import { useMeetups } from '../context/MeetupsContext';

// ─── Categories ────────────────────────────────────────────────────────────────
const CATEGORIES = [
  { id: "all", label: "All", emoji: "✨" },
  { id: "street", label: "Street Food", emoji: "🌮" },
  { id: "home", label: "Home Cooked", emoji: "🍲" },
  { id: "fine", label: "Fine Dining", emoji: "🍷" },
  { id: "brunch", label: "Brunch", emoji: "🥞" },
  { id: "bbq", label: "BBQ", emoji: "🔥" },
  { id: "vegan", label: "Vegan", emoji: "🥗" },
];

export interface MeetupPhotoResponse {
  id: number;
  image_url: string;
  user_id: string;
  created_at: string;
}

interface MeetupData {
  id: number;
  title: string;
  description: string | null;
  location: string;
  event_date?: string | null;
  host: { username: string; profile_picture_url?: string | null; bio?: string | null } | null;
  attendee_count: number;
  max_attendees: number;
  spots_left?: number;
  image_url?: string | null;
  photos?: MeetupPhotoResponse[];
}

// ─── Animated Category Pill ────────────────────────────────────────────────────
function CategoryPill({
  item,
  isActive,
  onPress,
  index,
}: {
  item: (typeof CATEGORIES)[0];
  isActive: boolean;
  onPress: () => void;
  index: number;
}) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = useCallback(() => {
    scale.value = withSpring(0.92, { damping: 15, stiffness: 300 });
  }, [scale]);

  const handlePressOut = useCallback(() => {
    scale.value = withSpring(1, { damping: 15, stiffness: 300 });
  }, [scale]);

  return (
    <Animated.View
      entering={FadeInRight.delay(100 + index * 60).duration(400)}
    >
      <Animated.View style={animatedStyle}>
        <Pressable
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          onPress={onPress}
          style={[
            styles.pill,
            isActive ? styles.pillActive : styles.pillInactive,
          ]}
        >
          <Text style={styles.pillEmoji}>{item.emoji}</Text>
          <Text
            style={[
              styles.pillLabel,
              isActive ? styles.pillLabelActive : styles.pillLabelInactive,
            ]}
          >
            {item.label}
          </Text>
        </Pressable>
      </Animated.View>
    </Animated.View>
  );
}

// ─── Featured Card ─────────────────────────────────────────────────────────────
function FeaturedCard({
  meetup,
  index,
}: {
  meetup: MeetupData;
  index: number;
}) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = useCallback(() => {
    scale.value = withSpring(0.97, { damping: 15, stiffness: 300 });
  }, [scale]);

  const handlePressOut = useCallback(() => {
    scale.value = withSpring(1, { damping: 15, stiffness: 300 });
  }, [scale]);

  const spotsLeft = meetup.spots_left ?? (meetup.max_attendees - (meetup.attendee_count || 0));
  const fillPercent = Math.min(((meetup.attendee_count || 0) / (meetup.max_attendees || 1)) * 100, 100);
  
  const accentColor = getCardColor(index);
  const emoji = getCardEmoji(index);
  
  const formattedDate = meetup.event_date ? new Date(meetup.event_date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) : 'TBD';
  const formattedTime = meetup.event_date ? new Date(meetup.event_date).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }) : 'TBD';

  return (
    <Animated.View
      entering={FadeInDown.delay(200 + index * 120)
        .duration(500)
        .springify()
        .damping(18)}
    >
      <Animated.View style={animatedStyle}>
        <Pressable
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          style={styles.featuredCardOuter}
        >
          {/* Accent top border */}
          <View
            style={[
              styles.featuredAccentBar,
              { backgroundColor: accentColor },
            ]}
          />

          <View style={styles.featuredCard}>
            {/* Header row */}
            {meetup.image_url ? (
              <View style={{ marginHorizontal: -22, marginTop: -22, marginBottom: 14, height: 150 }}>
                <Image source={{ uri: meetup.image_url }} style={{ width: '100%', height: '100%', borderTopLeftRadius: 20, borderTopRightRadius: 20 }} resizeMode="cover" />
                <View style={[styles.featuredBadgeRow, { position: 'absolute', bottom: 12, right: 12 }]}>
                  <View style={[styles.dateBadge, { backgroundColor: softBg(C.accent, 0.9) }]}>
                    <Text style={styles.dateBadgeText}>{formattedDate}</Text>
                  </View>
                  <View style={[styles.timeBadge, { backgroundColor: softBg(C.purple, 0.9) }]}>
                    <Text style={styles.timeBadgeText}>{formattedTime}</Text>
                  </View>
                </View>
              </View>
            ) : (
              <View style={styles.featuredHeader}>
                <View
                  style={[
                    styles.featuredEmojiWrap,
                    { backgroundColor: softBg(accentColor, 0.12) },
                  ]}
                >
                  <Text style={styles.featuredEmoji}>{emoji}</Text>
                </View>
                <View style={styles.featuredBadgeRow}>
                  <View
                    style={[
                      styles.dateBadge,
                      { backgroundColor: softBg(C.accent, 0.15) },
                    ]}
                  >
                    <Text style={styles.dateBadgeText}>{formattedDate}</Text>
                  </View>
                  <View
                    style={[
                      styles.timeBadge,
                      { backgroundColor: softBg(C.purple, 0.1) },
                    ]}
                  >
                    <Text style={styles.timeBadgeText}>{formattedTime}</Text>
                  </View>
                </View>
              </View>
            )}

            {/* Content */}
            <Text style={styles.featuredTitle}>{meetup.title}</Text>
            {meetup.description && (
              <Text style={styles.featuredDesc} numberOfLines={2}>
                {meetup.description}
              </Text>
            )}

            {/* Location */}
            <View style={styles.metaRow}>
              <Text style={styles.metaIcon}>📍</Text>
              <Text style={styles.metaText}>{meetup.location}</Text>
            </View>

            {/* Host */}
            <View style={styles.metaRow}>
              <Text style={styles.metaIcon}>👤</Text>
              <Text style={styles.metaText}>
                Hosted by{" "}
                <Text style={{ color: C.primary, fontWeight: "700" }}>
                  {meetup.host?.username || 'Unknown'}
                </Text>
              </Text>
            </View>

            {/* Gallery Mini Carousel */}
            {meetup.photos && meetup.photos.length > 0 && (
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 12 }} contentContainerStyle={{ paddingRight: 10 }}>
                {meetup.photos.map(photo => (
                  <Image key={photo.id} source={{ uri: photo.image_url }} style={{ width: 64, height: 64, borderRadius: 12, marginRight: 8, backgroundColor: C.border }} />
                ))}
              </ScrollView>
            )}

            {/* Footer: attendee bar */}
            <View style={styles.featuredFooter}>
              <View style={styles.attendeeInfo}>
                <View style={styles.attendeeBarTrack}>
                  <View
                    style={[
                      styles.attendeeBarFill,
                      {
                        width: `${fillPercent}%`,
                        backgroundColor: accentColor,
                      },
                    ]}
                  />
                </View>
                <Text style={styles.attendeeText}>
                  {meetup.attendee_count || 0}/{meetup.max_attendees} joined
                </Text>
              </View>
              <View
                style={[
                  styles.spotsBadge,
                  spotsLeft <= 3 && {
                    backgroundColor: "rgba(231,76,60,0.1)",
                  },
                ]}
              >
                <Text
                  style={[
                    styles.spotsText,
                    spotsLeft <= 3 && { color: "#E74C3C" },
                  ]}
                >
                  {spotsLeft} spot{spotsLeft !== 1 ? "s" : ""} left
                </Text>
              </View>
            </View>
          </View>
        </Pressable>
      </Animated.View>
    </Animated.View>
  );
}

// ─── Small Card (Popular Near You) ─────────────────────────────────────────────
function SmallCard({ meetup, index }: { meetup: MeetupData; index: number }) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = useCallback(() => {
    scale.value = withSpring(0.95, { damping: 15, stiffness: 300 });
  }, [scale]);

  const handlePressOut = useCallback(() => {
    scale.value = withSpring(1, { damping: 15, stiffness: 300 });
  }, [scale]);

  const accentColor = getCardColor(index);
  const emoji = getCardEmoji(index);
  
  const formattedDate = meetup.event_date ? new Date(meetup.event_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : 'TBD';

  return (
    <Animated.View
      entering={FadeInRight.delay(300 + index * 100).duration(450)}
    >
      <Animated.View style={animatedStyle}>
        <Pressable
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          style={styles.smallCardOuter}
        >
          {/* Accent left border */}
          <View
            style={[
              styles.smallAccentBar,
              { backgroundColor: accentColor },
            ]}
          />

          <View style={styles.smallCard}>
            {/* Top: Emoji & Category */}
            {meetup.image_url ? (
              <View style={{ marginHorizontal: -16, marginTop: -16, marginBottom: 10, height: 100 }}>
                <Image source={{ uri: meetup.image_url }} style={{ width: '100%', height: '100%', borderTopRightRadius: 18 }} resizeMode="cover" />
                <View style={[styles.smallCategoryBadge, { position: 'absolute', top: 8, right: 8, backgroundColor: 'rgba(255,255,255,0.9)' }]}>
                  <Text style={styles.smallCategoryText}>Meetup</Text>
                </View>
              </View>
            ) : (
              <View style={styles.smallHeader}>
                <View
                  style={[
                    styles.smallEmojiWrap,
                    { backgroundColor: softBg(accentColor, 0.12) },
                  ]}
                >
                  <Text style={styles.smallEmoji}>{emoji}</Text>
                </View>
                <View style={styles.smallCategoryBadge}>
                  <Text style={styles.smallCategoryText}>Meetup</Text>
                </View>
              </View>
            )}

            <Text style={styles.smallTitle} numberOfLines={2}>
              {meetup.title}
            </Text>

            <View style={[styles.metaRow, { marginTop: 8 }]}>
              <Text style={[styles.metaIcon, { fontSize: 12 }]}>📍</Text>
              <Text
                style={[styles.metaText, { fontSize: 12 }]}
                numberOfLines={1}
              >
                {meetup.location}
              </Text>
            </View>

            {/* Mini Gallery */}
            {meetup.photos && meetup.photos.length > 0 && (
              <View style={{ flexDirection: 'row', marginTop: 8, paddingLeft: 4 }}>
                {meetup.photos.slice(0, 4).map((photo, i) => (
                  <Image key={photo.id} source={{ uri: photo.image_url }} style={{ width: 26, height: 26, borderRadius: 13, marginLeft: -8, borderWidth: 1.5, borderColor: C.card, zIndex: 10 - i, backgroundColor: C.border }} />
                ))}
              </View>
            )}

            {/* Footer */}
            <View style={styles.smallFooter}>
              <Text style={styles.smallDate}>{formattedDate}</Text>
              <View style={styles.smallAttendeeBadge}>
                <Text style={styles.smallAttendeeText}>
                  {meetup.attendee_count || 0}👥
                </Text>
              </View>
            </View>
          </View>
        </Pressable>
      </Animated.View>
    </Animated.View>
  );
}

// ─── Main Screen ───────────────────────────────────────────────────────────────
export default function ExploreScreen() {
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const { meetups, loadMoreMeetups, hasMoreMeetups, loadingMore } = useMeetups();
  
  // Category heuristic to assign a category to meetups without one in the DB
  const getCategoryForMeetup = useCallback((meetup: MeetupData) => {
    const text = (meetup.title + " " + (meetup.description || "")).toLowerCase();
    const keywords: Record<string, string[]> = {
      street: ['street', 'truck', 'cart', 'taco', 'burger', 'pizza', 'fast'],
      home: ['home', 'family', 'grandma', 'cooked', 'homemade', 'stew', 'soup', 'bake'],
      fine: ['fine', 'fancy', 'wine', 'steak', 'gourmet', 'elegant', 'chef', 'tasting'],
      brunch: ['brunch', 'breakfast', 'pancake', 'egg', 'morning', 'coffee', 'cafe', 'mimosa'],
      bbq: ['bbq', 'barbeque', 'barbecue', 'grill', 'smoke', 'ribs', 'brisket', 'meat'],
      vegan: ['vegan', 'vegetarian', 'plant', 'healthy', 'salad', 'green', 'organic', 'raw'],
    };
    for (const [cat, words] of Object.entries(keywords)) {
      if (words.some(w => text.includes(w))) return cat;
    }
    // Fallback based on ID so every meetup gets a fun category
    const fallbackCategories = CATEGORIES.map(c => c.id).filter(id => id !== 'all');
    return fallbackCategories[meetup.id % fallbackCategories.length];
  }, []);

  // Filter meetups
  const filteredMeetups = meetups.filter((m: MeetupData) => {
    // 1. Search Query Filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = m.title.toLowerCase().includes(q);
      const matchLoc = m.location.toLowerCase().includes(q);
      const matchHost = m.host?.username?.toLowerCase().includes(q);
      if (!matchTitle && !matchLoc && !matchHost) return false;
    }
    
    // 2. Category Filter
    if (activeCategory !== 'all') {
      const cat = getCategoryForMeetup(m);
      if (cat !== activeCategory) return false;
    }
    
    return true;
  });

  // Split filtered meetups into featured and popular
  const featuredMeetups = filteredMeetups.slice(0, Math.ceil(filteredMeetups.length / 2));
  const popularMeetups = filteredMeetups.slice(Math.ceil(filteredMeetups.length / 2));

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <StatusBar style="dark" />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={16}
        onScroll={({ nativeEvent }) => {
          const { layoutMeasurement, contentOffset, contentSize } = nativeEvent;
          const isCloseToBottom = layoutMeasurement.height + contentOffset.y >= contentSize.height - 50;
          if (isCloseToBottom && !loadingMore && hasMoreMeetups) {
            loadMoreMeetups();
          }
        }}
      >
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <Animated.View
          entering={FadeInDown.delay(50).duration(500)}
          style={styles.header}
        >
          <Text style={styles.headerTitle}>Discover</Text>
          <Text style={styles.headerSubtitle}>
            Find your next food adventure
          </Text>
        </Animated.View>

        {/* ── Search Bar ─────────────────────────────────────────────────── */}
        <Animated.View
          entering={FadeInDown.delay(120).duration(450)}
          style={styles.searchContainer}
        >
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Search meetups, cuisines, hosts..."
            placeholderTextColor={C.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          <View style={styles.searchFilterBtn}>
            <Text style={styles.searchFilterIcon}>⚙️</Text>
          </View>
        </Animated.View>

        {/* ── Category Pills ─────────────────────────────────────────────── */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.pillsContainer}
          style={styles.pillsScroll}
        >
          {CATEGORIES.map((cat, idx) => (
            <CategoryPill
              key={cat.id}
              item={cat}
              isActive={activeCategory === cat.id}
              onPress={() => setActiveCategory(cat.id)}
              index={idx}
            />
          ))}
        </ScrollView>

        {/* ── Featured Section ───────────────────────────────────────────── */}
        {featuredMeetups.length > 0 && (
          <Animated.View
            entering={FadeIn.delay(300).duration(400)}
            style={styles.sectionHeader}
          >
            <View>
              <Text style={styles.sectionTitle}>Featured Meetups</Text>
              <Text style={styles.sectionSubtitle}>
                Hand-picked experiences for you
              </Text>
            </View>
            <TouchableOpacity style={styles.seeAllBtn}>
              <Text style={styles.seeAllText}>See all</Text>
            </TouchableOpacity>
          </Animated.View>
        )}

        {featuredMeetups.map((meetup: MeetupData, index: number) => (
          <FeaturedCard key={meetup.id} meetup={meetup} index={index} />
        ))}

        {/* ── Popular Near You Section ───────────────────────────────────── */}
        {popularMeetups.length > 0 && (
          <>
            <Animated.View
              entering={FadeIn.delay(600).duration(400)}
              style={[styles.sectionHeader, { marginTop: 32 }]}
            >
              <View>
                <Text style={styles.sectionTitle}>Popular Near You</Text>
                <Text style={styles.sectionSubtitle}>
                  Happening in your neighborhood
                </Text>
              </View>
              <TouchableOpacity style={styles.seeAllBtn}>
                <Text style={styles.seeAllText}>See all</Text>
              </TouchableOpacity>
            </Animated.View>

            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              snapToInterval={SMALL_CARD_W + 14}
              decelerationRate="fast"
              contentContainerStyle={styles.popularList}
            >
              {popularMeetups.map((item: MeetupData, index: number) => (
                <SmallCard key={item.id} meetup={item} index={index} />
              ))}
            </ScrollView>
          </>
        )}

        {filteredMeetups.length === 0 && !loadingMore && (
          <Animated.View entering={FadeIn.delay(200)} style={{ alignItems: 'center', marginTop: 60, paddingHorizontal: 32 }}>
            <Text style={{ fontSize: 48, marginBottom: 16 }}>🔍</Text>
            <Text style={{ fontSize: 20, fontWeight: '700', color: C.text, marginBottom: 8, textAlign: 'center' }}>No meetups found</Text>
            <Text style={{ fontSize: 15, color: C.textSecondary, textAlign: 'center', lineHeight: 22 }}>
              Try adjusting your search or category filter to find more delicious events.
            </Text>
          </Animated.View>
        )}

        {/* ── Bottom spacer for tab bar ──────────────────────────────────── */}
        <View style={{ height: 40 }} />
        {loadingMore && (
          <ActivityIndicator style={{ marginBottom: 60 }} color={C.primary} />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

// ─── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },

  // Header
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 4,
  },
  headerTitle: {
    fontSize: 34,
    fontWeight: "800",
    color: C.text,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 15,
    color: C.textSecondary,
    marginTop: 4,
    fontWeight: "500",
  },

  // Search
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: C.searchBg,
    borderRadius: 16,
    marginHorizontal: 24,
    marginTop: 20,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: C.cardBorder,
    ...SHADOW_SM,
  },
  searchIcon: {
    fontSize: 18,
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: C.text,
    fontWeight: "500",
    padding: 0,
  },
  searchFilterBtn: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: "#F5F5F5",
    alignItems: "center",
    justifyContent: "center",
  },
  searchFilterIcon: {
    fontSize: 16,
  },

  // Pills
  pillsScroll: {
    marginTop: 20,
  },
  pillsContainer: {
    paddingHorizontal: 24,
    gap: 10,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 24,
    gap: 6,
  },
  pillActive: {
    backgroundColor: C.primary,
  },
  pillInactive: {
    backgroundColor: "transparent",
    borderWidth: 1.5,
    borderColor: C.cardBorder,
  },
  pillEmoji: {
    fontSize: 15,
  },
  pillLabel: {
    fontSize: 14,
    fontWeight: "700",
  },
  pillLabelActive: {
    color: "#FFFFFF",
  },
  pillLabelInactive: {
    color: C.textSecondary,
  },

  // Section Header
  sectionHeader: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    paddingHorizontal: 24,
    marginTop: 28,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: C.text,
    letterSpacing: -0.3,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: C.textSecondary,
    marginTop: 2,
    fontWeight: "500",
  },
  seeAllBtn: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 20,
    backgroundColor: "rgba(255,45,120,0.08)",
  },
  seeAllText: {
    color: C.primary,
    fontSize: 13,
    fontWeight: "700",
  },

  // Featured Card
  featuredCardOuter: {
    marginHorizontal: 24,
    marginBottom: 16,
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: C.card,
    ...SHADOW_MD,
  },
  featuredAccentBar: {
    height: 4,
    width: "100%",
  },
  featuredCard: {
    backgroundColor: C.card,
    padding: 22,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  featuredHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  featuredEmojiWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  featuredEmoji: {
    fontSize: 24,
  },
  featuredBadgeRow: {
    flexDirection: "row",
    gap: 8,
  },
  dateBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
  },
  dateBadgeText: {
    color: "#B8860B",
    fontSize: 12,
    fontWeight: "700",
  },
  timeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
  },
  timeBadgeText: {
    color: C.purple,
    fontSize: 12,
    fontWeight: "700",
  },
  featuredTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: C.text,
    letterSpacing: -0.3,
    marginBottom: 6,
  },
  featuredDesc: {
    fontSize: 14,
    color: C.textSecondary,
    lineHeight: 20,
    marginBottom: 14,
    fontWeight: "500",
  },

  // Meta rows
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
    gap: 6,
  },
  metaIcon: {
    fontSize: 14,
  },
  metaText: {
    fontSize: 13,
    color: C.textSecondary,
    fontWeight: "500",
    flexShrink: 1,
  },

  // Footer / attendee bar
  featuredFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: C.cardBorder,
  },
  attendeeInfo: {
    flex: 1,
    marginRight: 14,
  },
  attendeeBarTrack: {
    height: 5,
    backgroundColor: "#F0F0F0",
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 6,
  },
  attendeeBarFill: {
    height: "100%",
    borderRadius: 3,
  },
  attendeeText: {
    fontSize: 12,
    color: C.textSecondary,
    fontWeight: "600",
  },
  spotsBadge: {
    backgroundColor: "rgba(255,198,41,0.15)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  spotsText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#B8860B",
  },

  // Popular / Small cards
  popularList: {
    paddingHorizontal: 24,
    gap: 14,
  },
  smallCardOuter: {
    width: SMALL_CARD_W,
    borderRadius: 18,
    overflow: "hidden",
    flexDirection: "row",
    backgroundColor: C.card,
    ...SHADOW_SM,
  },
  smallAccentBar: {
    width: 4,
    height: "100%",
  },
  smallCard: {
    flex: 1,
    backgroundColor: C.card,
    padding: 16,
    borderTopRightRadius: 18,
    borderBottomRightRadius: 18,
  },
  smallHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  smallEmojiWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  smallEmoji: {
    fontSize: 18,
  },
  smallCategoryBadge: {
    backgroundColor: "#F5F5F5",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  smallCategoryText: {
    fontSize: 10,
    fontWeight: "700",
    color: C.textSecondary,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  smallTitle: {
    fontSize: 15,
    fontWeight: "800",
    color: C.text,
    letterSpacing: -0.2,
  },
  smallFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: C.cardBorder,
  },
  smallDate: {
    fontSize: 11,
    color: C.primary,
    fontWeight: "700",
  },
  smallAttendeeBadge: {
    backgroundColor: "#F5F5F5",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  smallAttendeeText: {
    fontSize: 11,
    fontWeight: "700",
    color: C.textSecondary,
  },
});
