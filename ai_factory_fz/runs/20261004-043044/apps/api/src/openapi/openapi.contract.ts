import { readFileSync } from 'fs';
import { load } from 'js-yaml';
import { join } from 'path';

const OPENAPI_RELATIVE_PATH = 'openapi.yaml';

export type ContractOpenApiDocument = Record<string, unknown>;

export function loadContractOpenApiDocument(): ContractOpenApiDocument {
  const openApiPath = join(process.cwd(), OPENAPI_RELATIVE_PATH);
  return load(readFileSync(openApiPath, 'utf8')) as ContractOpenApiDocument;
}
