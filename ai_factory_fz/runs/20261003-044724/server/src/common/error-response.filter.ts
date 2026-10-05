import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
} from '@nestjs/common';

/**
 * Ensures every HTTP error body matches the OpenAPI ErrorResponse contract:
 * `{ statusCode, error, message }` (additionalProperties: false).
 *
 * Nest's default handler already shapes HttpException responses correctly, but
 * unexpected (non-HttpException) failures fall back to
 * `{ statusCode: 500, message: 'Internal server error' }` with no `error`
 * field — which breaks strict clients generated from docs/openapi.yaml.
 */
@Catch()
export class ErrorResponseFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const response = host.switchToHttp().getResponse<{
      status: (code: number) => { json: (body: unknown) => void };
    }>();

    if (exception instanceof HttpException) {
      const statusCode = exception.getStatus();
      const raw = exception.getResponse();
      if (typeof raw === 'string') {
        response.status(statusCode).json({
          statusCode,
          error: statusLabel(statusCode),
          message: raw,
        });
        return;
      }

      const body = raw as Record<string, unknown>;
      const error =
        typeof body.error === 'string' && body.error.length > 0
          ? body.error
          : statusLabel(statusCode);
      const message =
        typeof body.message === 'string'
          ? body.message
          : Array.isArray(body.message)
            ? String(body.message[0] ?? statusLabel(statusCode))
            : statusLabel(statusCode);

      response.status(statusCode).json({
        statusCode,
        error,
        message,
      });
      return;
    }

    response.status(HttpStatus.INTERNAL_SERVER_ERROR).json({
      statusCode: HttpStatus.INTERNAL_SERVER_ERROR,
      error: 'Internal Server Error',
      message: 'Internal server error',
    });
  }
}

function statusLabel(statusCode: number): string {
  switch (statusCode) {
    case HttpStatus.BAD_REQUEST:
      return 'Bad Request';
    case HttpStatus.UNAUTHORIZED:
      return 'Unauthorized';
    case HttpStatus.FORBIDDEN:
      return 'Forbidden';
    case HttpStatus.NOT_FOUND:
      return 'Not Found';
    case HttpStatus.CONFLICT:
      return 'Conflict';
    case HttpStatus.SERVICE_UNAVAILABLE:
      return 'Service Unavailable';
    case HttpStatus.INTERNAL_SERVER_ERROR:
      return 'Internal Server Error';
    default:
      return 'Error';
  }
}
