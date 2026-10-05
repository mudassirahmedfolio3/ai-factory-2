// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { ArgumentsHost, Catch, ExceptionFilter, HttpException, HttpStatus } from '@nestjs/common';

/** Every error leaves the API as the shared Error schema from docs/openapi.yaml: { code, message }. */
@Catch()
export class ErrorFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const res = host.switchToHttp().getResponse();
    if (exception instanceof HttpException) {
      const body = exception.getResponse() as any;
      const status = exception.getStatus();
      const message = Array.isArray(body?.message) ? body.message.join('; ') : body?.message ?? exception.message;
      res.status(status).json({ code: body?.code ?? (status === 400 ? 'VALIDATION_ERROR' : 'ERROR'), message });
      return;
    }
    res.status(HttpStatus.INTERNAL_SERVER_ERROR).json({ code: 'INTERNAL', message: 'Unexpected error' });
  }
}
