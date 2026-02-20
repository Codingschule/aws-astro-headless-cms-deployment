/**
 *
 * Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format
 * @param {Object} event - API Gateway Lambda Proxy Input Format
 *
 * Context doc: https://docs.aws.amazon.com/lambda/latest/dg/nodejs-prog-model-context.html 
 * @param {Object} context
 *
 * Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
 * @returns {Object} object - API Gateway Lambda Proxy Output Format
 * 
 */

import { DynamoDBClient, PutItemCommand, ScanCommand } from "@aws-sdk/client-dynamodb";

const DEBUG = process.env.DEBUG === 'true';
const client = new DynamoDBClient({});

const corsMode = parseInt(process.env.CORS_MODE ?? '', 10) || 1;
const cloudFrontDomain = process.env.CORS_CLOUDFRONT_DOMAIN ?? '';

function getCorsHeaders(origin) {
  if (corsMode === 0) return {};
  
  const allowedOrigins = [];
  
  if (corsMode >= 1 && cloudFrontDomain) {
    allowedOrigins.push(cloudFrontDomain);
  }
  if (corsMode >= 2) {
    allowedOrigins.push('http://localhost:4321', 'http://127.0.0.1:4321');
  }
  
  if (corsMode === 3) {
    return { 
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type'
    };
  }
  
  if (origin && allowedOrigins.includes(origin)) {
    return { 
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Headers': 'Content-Type'
    };
  }
  
  return {};
}

function debugLog(message, data = null) {
  if (!DEBUG) return;
  if (data) {
    console.warn(`[DEBUG] ${message}:`, JSON.stringify(data, null, 2));
  } else {
    console.warn(`[DEBUG] ${message}`);
  }
}

function errorLog(message, data = null) {
  if (data) {
    console.error(`[ERROR] ${message}:`, JSON.stringify(data, null, 2));
  } else {
    console.error(`[ERROR] ${message}`);
  }
}

export const lambda_handler = async (event, context) => {
  debugLog('=== Lambda invoked ===');
  debugLog('Event', event);
  debugLog('Context (functionName, functionVersion, requestId)', {
    functionName: context.functionName,
    functionVersion: context.functionVersion,
    requestId: context.requestId,
    memoryLimitInMB: context.memoryLimitInMB,
  });
  debugLog('Environment Variables', {
    TABLE_NAME: process.env.TABLE_NAME,
    DEBUG: process.env.DEBUG,
    AWS_REGION: process.env.AWS_REGION,
    AWS_LAMBDA_FUNCTION_NAME: process.env.AWS_LAMBDA_FUNCTION_NAME,
    CORS_MODE: process.env.CORS_MODE,
    CORS_CLOUDFRONT_DOMAIN: process.env.CORS_CLOUDFRONT_DOMAIN,
  });

  const method = event.httpMethod || 'GET';
  const origin = event.headers?.origin || event.headers?.Origin || '';
  const corsHeaders = getCorsHeaders(origin);
  debugLog('CORS Mode', { corsMode, origin, corsHeaders });

  if (method === 'OPTIONS') {
    return { statusCode: 204, headers: corsHeaders, body: '' };
  }

  const tableName = process.env.TABLE_NAME;
  debugLog('TABLE_NAME from env', tableName);

  if (!tableName) {
    errorLog('TABLE_NAME environment variable is NOT SET');
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'TABLE_NAME not set' }),
    };
  }

  if (method === 'POST') {
    debugLog('=== Handling POST request ===');
    let body;
    try {
      const rawBody = event.body;
      debugLog('Raw event.body type', typeof rawBody);
      debugLog('Raw event.body', rawBody);
      body = typeof rawBody === 'string' ? JSON.parse(rawBody) : rawBody;
      debugLog('Parsed body', body);
    } catch (e) {
      errorLog('JSON parse failed', e.message);
      return { statusCode: 400, headers: corsHeaders, body: JSON.stringify({ error: 'Invalid JSON' }) };
    }
    const { name, message } = body || {};
    if (!name || !message) {
      errorLog('Missing required fields', { name, message });
      return { statusCode: 400, headers: corsHeaders, body: JSON.stringify({ error: 'Missing name or message' }) };
    }
    const id = Date.now().toString();
    const item = {
      id: { S: id },
      name: { S: name },
      message: { S: message },
      createdAt: { S: new Date().toISOString() },
    };
    debugLog('Attempting to write to DynamoDB', { tableName, item });
    try {
      await client.send(new PutItemCommand({ TableName: tableName, Item: item }));
      debugLog('DynamoDB PutItem SUCCESS', { id });
    } catch (e) {
      errorLog('DynamoDB PutItem FAILED', e);
      return { statusCode: 500, headers: corsHeaders, body: JSON.stringify({ error: 'DB write failed' }) };
    }
    const response = { id, name, message, createdAt: item.createdAt.S };
    debugLog('POST response', response);
    return { statusCode: 201, headers: corsHeaders, body: JSON.stringify(response) };
  }

  // GET
  debugLog('=== Handling GET request ===');
  debugLog('Attempting DynamoDB Scan', { tableName });
  try {
    const data = await client.send(new ScanCommand({ TableName: tableName }));
    debugLog('DynamoDB Scan SUCCESS', { itemCount: data.Items?.length });
    const items = (data.Items || []).map(i => ({
      id: i.id.S,
      name: i.name.S,
      message: i.message.S,
      createdAt: i.createdAt.S
    }));
    debugLog('GET response', { entryCount: items.length, items });
    return { statusCode: 200, headers: corsHeaders, body: JSON.stringify({ entries: items }) };
  } catch (e) {
    errorLog('DynamoDB Scan FAILED', e);
    return { statusCode: 500, headers: corsHeaders, body: JSON.stringify({ error: 'DB read failed' }) };
  }
};