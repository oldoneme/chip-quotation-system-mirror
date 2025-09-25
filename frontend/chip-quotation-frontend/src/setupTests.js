// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

jest.mock('axios');

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

jest.mock('antd/lib/_util/responsiveObserver', () => ({
  __esModule: true,
  default: () => ({
    responsiveMap: {},
    matchHandlers: {},
    subscribe: () => 0,
    unsubscribe: () => {},
    dispatch: () => false,
  }),
  responsiveArray: ['xxl', 'xl', 'lg', 'md', 'sm', 'xs'],
  matchScreen: () => undefined,
}));

const sessionStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value?.toString() ?? ''; },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});
