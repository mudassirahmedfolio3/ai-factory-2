import {
  M3_API_OPERATIONS,
  M3_COUNTED_OPERATIONS,
  M3_HEALTH_OPERATION,
} from './m3-api.operations';

describe('M3 API operation registry', () => {
  it('lists twenty-eight counted operations and getHealth', () => {
    expect(M3_COUNTED_OPERATIONS).toHaveLength(28);
    expect(M3_API_OPERATIONS).toHaveLength(29);
    expect(M3_API_OPERATIONS[0]).toEqual(M3_HEALTH_OPERATION);
  });

  it('uses unique operationIds', () => {
    const ids = M3_API_OPERATIONS.map((op) => op.operationId);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
