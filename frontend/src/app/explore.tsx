import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Dimensions,
  Pressable,
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

// ─── Colors ────────────────────────────────────────────────────────────────────
const C = {
  bg: "#FFFDF9",
  card: "#FFFFFF",
  cardBorder: "#EBEBEB",
  primary: "#FF2D78",
  primaryLight: "#FF6B9D",
  accent: "#FFC629",
  purple: "#8B5CF6",
  text: "#222222",
  textSecondary: "#717171",
  searchBg: "#FFFFFF",
} as const;

const { width: SCREEN_W } = Dimensions.get("window");
const SMALL_CARD_W = SCREEN_W * 0.52;

// ─── Shadow Tiers ──────────────────────────────────────────────────────────────
const SHADOW_SM = {
  shadowColor: "#000",
  shadowOffset: { width: 0, height: 1 },
  shadowOpacity: 0.04,
  shadowRadius: 3,
  elevation: 1,
};

const SHADOW_MD = {
  shadowColor: "#000",
  shadowOffset: { width: 0, height: 3 },
  shadowOpacity: 0.07,
  shadowRadius: 8,
  elevation: 3,
};

// ─── Mock Data ─────────────────────────────────────────────────────────────────
const CATEGORIES = [
  { id: "all", label: "All", emoji: "✨" },
  { id: "street", label: "Street Food", emoji: "🌮" },
  { id: "home", label: "Home Cooked", emoji: "🍲" },
  { id: "fine", label: "Fine Dining", emoji: "🍷" },
  { id: "brunch", label: "Brunch", emoji: "🥞" },
  { id: "bbq", label: "BBQ", emoji: "🔥" },
  { id: "vegan", label: "Vegan", emoji: "🥗" },
];

interface Meetup {
  id: string;
  title: string;
  description: string;
  location: string;
  host: string;
  attendees: number;
  maxAttendees: number;
  date: string;
  time: string;
  category: string;
  emoji: string;
  accentColor: string;
}

const FEATURED_MEETUPS: Meetup[] = [
  {
    id: "f1",
    title: "Midnight Taco Crawl",
    description:
      "Explore the best late-night taco stands with fellow food lovers. We'll hit 4 spots in one epic night.",
    location: "Downtown Arts District",
    host: "Carlos M.",
    attendees: 12,
    maxAttendees: 16,
    date: "Sat, Jun 21",
    time: "9:00 PM",
    category: "Street Food",
    emoji: "🌮",
    accentColor: C.primary,
  },
  {
    id: "f2",
    title: "Sunday Brunch Club",
    description:
      "A relaxed Sunday morning with homemade waffles, fresh juice, and great conversations.",
    location: "Maple Street Kitchen",
    host: "Priya K.",
    attendees: 7,
    maxAttendees: 10,
    date: "Sun, Jun 22",
    time: "10:30 AM",
    category: "Brunch",
    emoji: "🥞",
    accentColor: C.accent,
  },
  {
    id: "f3",
    title: "Vegan Sushi Night",
    description:
      "Learn to roll plant-based sushi with a professional chef. All ingredients provided!",
    location: "Green Leaf Studio",
    host: "Yuki T.",
    attendees: 9,
    maxAttendees: 12,
    date: "Fri, Jun 20",
    time: "7:00 PM",
    category: "Vegan",
    emoji: "🍣",
    accentColor: "#4ECDC4",
  },
];

const POPULAR_MEETUPS: Meetup[] = [
  {
    id: "p1",
    title: "BBQ & Blues Jam",
    description: "Smoked ribs, brisket, and live blues guitar in the backyard.",
    location: "Oakwood Park",
    host: "James R.",
    attendees: 18,
    maxAttendees: 25,
    date: "Sat, Jun 21",
    time: "4:00 PM",
    category: "BBQ",
    emoji: "🔥",
    accentColor: "#E74C3C",
  },
  {
    id: "p2",
    title: "Nonna's Pasta Night",
    description: "Handmade pasta from scratch — just like grandma used to make.",
    location: "Little Italy Kitchen",
    host: "Maria L.",
    attendees: 6,
    maxAttendees: 8,
    date: "Thu, Jun 19",
    time: "6:30 PM",
    category: "Home Cooked",
    emoji: "🍝",
    accentColor: C.primary,
  },
  {
    id: "p3",
    title: "Omakase Experience",
    description: "An intimate 8-course chef's tasting with sake pairings.",
    location: "Koi House",
    host: "Chef Tanaka",
    attendees: 4,
    maxAttendees: 6,
    date: "Fri, Jun 20",
    time: "8:00 PM",
    category: "Fine Dining",
    emoji: "🍷",
    accentColor: "#9B59B6",
  },
  {
    id: "p4",
    title: "Chai & Chaat Walk",
    description: "Street food tour through the city's best chaat vendors.",
    location: "Old Market Quarter",
    host: "Arjun S.",
    attendees: 14,
    maxAttendees: 20,
    date: "Sun, Jun 22",
    time: "5:00 PM",
    category: "Street Food",
    emoji: "☕",
    accentColor: C.accent,
  },
];

// ─── Helper: soft tinted background from accent color ──────────────────────────
function softBg(hex: string, opacity: number = 0.1): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${opacity})`;
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
  meetup: Meetup;
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

  const spotsLeft = meetup.maxAttendees - meetup.attendees;
  const fillPercent = (meetup.attendees / meetup.maxAttendees) * 100;

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
              { backgroundColor: meetup.accentColor },
            ]}
          />

          <View style={styles.featuredCard}>
            {/* Header row */}
            <View style={styles.featuredHeader}>
              <View
                style={[
                  styles.featuredEmojiWrap,
                  { backgroundColor: softBg(meetup.accentColor, 0.12) },
                ]}
              >
                <Text style={styles.featuredEmoji}>{meetup.emoji}</Text>
              </View>
              <View style={styles.featuredBadgeRow}>
                <View
                  style={[
                    styles.dateBadge,
                    { backgroundColor: softBg(C.accent, 0.15) },
                  ]}
                >
                  <Text style={styles.dateBadgeText}>{meetup.date}</Text>
                </View>
                <View
                  style={[
                    styles.timeBadge,
                    { backgroundColor: softBg(C.purple, 0.1) },
                  ]}
                >
                  <Text style={styles.timeBadgeText}>{meetup.time}</Text>
                </View>
              </View>
            </View>

            {/* Content */}
            <Text style={styles.featuredTitle}>{meetup.title}</Text>
            <Text style={styles.featuredDesc} numberOfLines={2}>
              {meetup.description}
            </Text>

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
                  {meetup.host}
                </Text>
              </Text>
            </View>

            {/* Footer: attendee bar */}
            <View style={styles.featuredFooter}>
              <View style={styles.attendeeInfo}>
                <View style={styles.attendeeBarTrack}>
                  <View
                    style={[
                      styles.attendeeBarFill,
                      {
                        width: `${fillPercent}%`,
                        backgroundColor: meetup.accentColor,
                      },
                    ]}
                  />
                </View>
                <Text style={styles.attendeeText}>
                  {meetup.attendees}/{meetup.maxAttendees} joined
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
function SmallCard({ meetup, index }: { meetup: Meetup; index: number }) {
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
              { backgroundColor: meetup.accentColor },
            ]}
          />

          <View style={styles.smallCard}>
            {/* Top: Emoji & Category */}
            <View style={styles.smallHeader}>
              <View
                style={[
                  styles.smallEmojiWrap,
                  { backgroundColor: softBg(meetup.accentColor, 0.12) },
                ]}
              >
                <Text style={styles.smallEmoji}>{meetup.emoji}</Text>
              </View>
              <View style={styles.smallCategoryBadge}>
                <Text style={styles.smallCategoryText}>{meetup.category}</Text>
              </View>
            </View>

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

            {/* Footer */}
            <View style={styles.smallFooter}>
              <Text style={styles.smallDate}>{meetup.date}</Text>
              <View style={styles.smallAttendeeBadge}>
                <Text style={styles.smallAttendeeText}>
                  {meetup.attendees}👥
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

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <StatusBar style="dark" />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
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
            editable={false}
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

        {FEATURED_MEETUPS.map((meetup, index) => (
          <FeaturedCard key={meetup.id} meetup={meetup} index={index} />
        ))}

        {/* ── Popular Near You Section ───────────────────────────────────── */}
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

        <FlatList
          data={POPULAR_MEETUPS}
          keyExtractor={(item) => item.id}
          horizontal
          showsHorizontalScrollIndicator={false}
          snapToInterval={SMALL_CARD_W + 14}
          decelerationRate="fast"
          contentContainerStyle={styles.popularList}
          renderItem={({ item, index }) => (
            <SmallCard meetup={item} index={index} />
          )}
          scrollEnabled
        />

        {/* ── Bottom spacer for tab bar ──────────────────────────────────── */}
        <View style={{ height: 100 }} />
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
