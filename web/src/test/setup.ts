import "@testing-library/jest-dom/vitest";

Object.defineProperty(HTMLElement.prototype, "clientWidth", {
  configurable: true,
  value: 960,
});

Object.defineProperty(HTMLElement.prototype, "clientHeight", {
  configurable: true,
  value: 540,
});

Object.defineProperty(HTMLElement.prototype, "getBoundingClientRect", {
  configurable: true,
  value() {
    return {
      width: 960,
      height: 540,
      top: 0,
      left: 0,
      right: 960,
      bottom: 540,
      x: 0,
      y: 0,
      toJSON() {
        return this;
      },
    };
  },
});
