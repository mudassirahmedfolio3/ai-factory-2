import {
  BadRequestException,
  HttpException,
  HttpStatus,
  NotFoundException,
} from '@nestjs/common';
import { describe, expect, it, vi } from 'vitest';
import { ErrorResponseFilter } from './error-response.filter.js';

function mockHost(response: {
  status: ReturnType<typeof vi.fn>;
}) {
  return {
    switchToHttp: () => ({
      getResponse: () => response,
    }),
  };
}

describe('ErrorResponseFilter', () => {
  const filter = new ErrorResponseFilter();

  it('shapes unexpected Error as { statusCode, error, message } 500', () => {
    const json = vi.fn();
    const status = vi.fn().mockReturnValue({ json });
    filter.catch(new Error('connection terminated unexpectedly'), mockHost({
      status,
    }) as never);

    expect(status).toHaveBeenCalledWith(HttpStatus.INTERNAL_SERVER_ERROR);
    expect(json).toHaveBeenCalledWith({
      statusCode: 500,
      error: 'Internal Server Error',
      message: 'Internal server error',
    });
  });

  it('does not leak unexpected error messages', () => {
    const json = vi.fn();
    const status = vi.fn().mockReturnValue({ json });
    filter.catch(new Error('password=secret db down'), mockHost({ status }) as never);

    const body = json.mock.calls[0]?.[0] as { message: string };
    expect(body.message).toBe('Internal server error');
    expect(body.message).not.toContain('password');
  });

  it('preserves HttpException contract fields including error', () => {
    const json = vi.fn();
    const status = vi.fn().mockReturnValue({ json });
    filter.catch(
      new NotFoundException("Product with id 'x' was not found"),
      mockHost({ status }) as never,
    );

    expect(status).toHaveBeenCalledWith(404);
    expect(json).toHaveBeenCalledWith({
      statusCode: 404,
      error: 'Not Found',
      message: "Product with id 'x' was not found",
    });
  });

  it('normalizes string HttpException responses to include error', () => {
    const json = vi.fn();
    const status = vi.fn().mockReturnValue({ json });
    filter.catch(
      new HttpException('boom', HttpStatus.BAD_GATEWAY),
      mockHost({ status }) as never,
    );

    expect(status).toHaveBeenCalledWith(HttpStatus.BAD_GATEWAY);
    expect(json).toHaveBeenCalledWith({
      statusCode: HttpStatus.BAD_GATEWAY,
      error: 'Error',
      message: 'boom',
    });
  });

  it('keeps BadRequestException message and error', () => {
    const json = vi.fn();
    const status = vi.fn().mockReturnValue({ json });
    filter.catch(
      new BadRequestException('priceBand must be a valid enum value'),
      mockHost({ status }) as never,
    );

    expect(status).toHaveBeenCalledWith(400);
    expect(json).toHaveBeenCalledWith({
      statusCode: 400,
      error: 'Bad Request',
      message: 'priceBand must be a valid enum value',
    });
  });
});
