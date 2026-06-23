import * as React from 'react';
import { render, screen } from '@testing-library/react-native';
import { ThemedText } from '../themed-text';

// Mock the useTheme hook since it relies on Context
jest.mock('@/hooks/use-theme', () => ({
  useTheme: () => ({
    text: '#000000',
    background: '#ffffff',
  }),
}));

describe('ThemedText', () => {
  it('renders correctly with default type', async () => {
    await render(<ThemedText>Hello World</ThemedText>);
    const element = screen.getByText('Hello World');
    expect(element).toBeTruthy();
    // In actual implementation, color comes from theme['text']
    expect(element.props.style).toContainEqual({ color: '#000000' });
  });

  it('renders correctly with title type', async () => {
    await render(<ThemedText type="title">Title Text</ThemedText>);
    const element = screen.getByText('Title Text');
    expect(element).toBeTruthy();
    expect(element.props.style).toContainEqual(expect.objectContaining({ fontSize: 48 }));
  });
});
