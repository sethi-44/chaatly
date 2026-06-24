// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const RealReanimated = jest.requireActual('react-native-reanimated');
  const Animated = {
    ...RealReanimated,
    View: 'Animated.View',
    Text: 'Animated.Text',
    Image: 'Animated.Image',
    ScrollView: 'Animated.ScrollView',
    FlatList: 'Animated.FlatList',
    SectionList: 'Animated.SectionList',
    useSharedValue: jest.fn(() => ({ value: 0 })),
    useAnimatedStyle: jest.fn(() => ({})),
    withSpring: jest.fn((val) => val),
    withTiming: jest.fn((val) => val),
    withSequence: jest.fn((...args) => args[args.length - 1]),
    withRepeat: jest.fn((val) => val),
    withDelay: jest.fn((val) => val),
    Easing: {
      inOut: jest.fn(() => 'ease'),
      ease: 'ease',
    },
  };
  
  // Create a chainable mock for animation presets
  const createAnimationMock = () => {
    const mock = {
      duration: jest.fn(() => mock),
      springify: jest.fn(() => mock),
      damping: jest.fn(() => mock),
      delay: jest.fn(() => mock),
    };
    return mock;
  };
  
  // Mock the animated components
  const createMockComponent = (name: string) => {
    const MockComponent = ({ children, style, entering, ...props }: any) => {
      return React.createElement(name, { ...props, style }, children);
    };
    MockComponent.displayName = `Animated.${name}`;
    return MockComponent;
  };
  
  const React = require('react');
  
  return {
    ...Animated,
    View: createMockComponent('View'),
    Text: createMockComponent('Text'),
    Image: createMockComponent('Image'),
    ScrollView: createMockComponent('ScrollView'),
    FlatList: createMockComponent('FlatList'),
    SectionList: createMockComponent('SectionList'),
    FadeInDown: createAnimationMock(),
    FadeInUp: createAnimationMock(),
    FadeInRight: createAnimationMock(),
    FadeIn: createAnimationMock(),
  };
});

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(() => Promise.resolve()),
  getItemAsync: jest.fn(() => Promise.resolve(null)),
  deleteItemAsync: jest.fn(() => Promise.resolve()),
}));

// Mock expo-router
jest.mock('expo-router', () => ({
  useLocalSearchParams: () => ({}),
  router: {
    replace: jest.fn(),
    push: jest.fn(),
  },
}));

// Mock react-native-safe-area-context
jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: ({ children }: any) => children,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

// Mock axios
jest.mock('axios', () => ({
  post: jest.fn(),
  get: jest.fn(),
  interceptors: {
    response: {
      use: jest.fn(),
      eject: jest.fn(),
    },
  },
}));