import { describe, it, expect } from 'vitest';

// Simple test to verify the test setup works
describe('Basic Tests', () => {
  it('should pass basic assertion', () => {
    expect(1 + 1).toBe(2);
  });
  
  it('should handle arrays', () => {
    const arr = [1, 2, 3];
    expect(arr).toHaveLength(3);
    expect(arr).toContain(2);
  });
  
  it('should handle objects', () => {
    const obj = { name: 'test', value: 42 };
    expect(obj.name).toBe('test');
    expect(obj.value).toBe(42);
  });
});
