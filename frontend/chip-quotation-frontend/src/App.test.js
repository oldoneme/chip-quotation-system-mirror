import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

jest.mock('./contexts/AuthContext', () => {
  const React = require('react');
  const noop = () => {};
  return {
    AuthProvider: ({ children }) => React.createElement(React.Fragment, null, children),
    useAuth: () => ({
      loading: false,
      authenticated: true,
      user: { name: 'Test User' },
      logout: noop,
      checkAuth: noop,
      refreshAuth: noop,
      setUser: noop,
    }),
  };
});

test('renders application shell once auth is ready', () => {
  render(<App />);
  expect(screen.getByText(/报价中心/)).toBeInTheDocument();
});
