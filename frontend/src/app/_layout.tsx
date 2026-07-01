import { Tabs } from "expo-router";
import { Text, View, StyleSheet, Platform } from "react-native";
import { ACTIVE_COLOR, INACTIVE_COLOR, TAB_BAR_BG, TAB_BAR_BORDER } from '../constants';
import { MeetupsProvider } from '../context/MeetupsContext';

function TabIcon({
  emoji,
  focused,
}: {
  emoji: string;
  focused: boolean;
}) {
  return (
    <View style={styles.iconContainer}>
      <Text
        style={[
          styles.icon,
          focused ? styles.iconActive : styles.iconInactive,
        ]}
      >
        {emoji}
      </Text>
      {focused && <View style={styles.activeGlow} />}
    </View>
  );
}

export default function RootLayout() {
  return (
    <MeetupsProvider>
      <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: ACTIVE_COLOR,
        tabBarInactiveTintColor: INACTIVE_COLOR,
        tabBarLabelStyle: styles.tabLabel,
        tabBarItemStyle: styles.tabBarItem,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ focused }) => (
            <TabIcon emoji="🏠" focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: "Explore",
          tabBarIcon: ({ focused }) => (
            <TabIcon emoji="🔍" focused={focused} />
          ),
        }}
      />

      {/* Hidden screens — not shown in the tab bar */}
      <Tabs.Screen
        name="verify-email"
        options={{
          href: null,
        }}
      />
      <Tabs.Screen
        name="reset-password"
        options={{
          href: null,
        }}
      />
    </Tabs>
    </MeetupsProvider>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: TAB_BAR_BG,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: TAB_BAR_BORDER,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    height: 70,
    paddingTop: 6,
    paddingBottom: Platform.OS === "ios" ? 20 : 10,
    paddingHorizontal: 16,
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    elevation: 12,
    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
      },
      android: {
        elevation: 12,
      },
    }),
  },
  tabBarItem: {
    paddingVertical: 4,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.3,
    marginTop: 2,
  },
  iconContainer: {
    alignItems: "center",
    justifyContent: "center",
    width: 36,
    height: 36,
  },
  icon: {
    fontSize: 24,
    textAlign: "center",
  },
  iconActive: {
    opacity: 1,
    transform: [{ scale: 1.12 }],
  },
  iconInactive: {
    opacity: 0.55,
    transform: [{ scale: 1.0 }],
  },
  activeGlow: {
    position: "absolute",
    bottom: -2,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: ACTIVE_COLOR,
    opacity: 0.7,
  },
});
