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

const client = new DynamoDBClient({});

export const lambda_handler = async (event, context) => {
  const method = event.httpMethod || 'GET';
  const tableName = process.env.TABLE_NAME;

  if (!tableName) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'TABLE_NAME not set' }),
    };
  }

  if (method === 'POST') {
    let body;
    try {
      body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    } catch (_) {
      return { statusCode: 400, body: JSON.stringify({ error: 'Invalid JSON' }) };
    }
    const { name, message } = body || {};
    if (!name || !message) {
      return { statusCode: 400, body: JSON.stringify({ error: 'Missing name or message' }) };
    }
    const id = Date.now().toString();
    const item = {
      id: { S: id },
      name: { S: name },
      message: { S: message },
      createdAt: { S: new Date().toISOString() },
    };
    try {
      await client.send(new PutItemCommand({ TableName: tableName, Item: item }));
    } catch (e) {
      return { statusCode: 500, body: JSON.stringify({ error: 'DB write failed' }) };
    }
    const response = { id, name, message, createdAt: item.createdAt.S };
    return { statusCode: 201, body: JSON.stringify(response) };
  }

  // GET
  try {
    const data = await client.send(new ScanCommand({ TableName: tableName }));
    const items = (data.Items || []).map(i => ({
      id: i.id.S,
      name: i.name.S,
      message: i.message.S,
      createdAt: i.createdAt.S
    }));
    return { statusCode: 200, body: JSON.stringify({ entries: items }) };
  } catch (e) {
    return { statusCode: 500, body: JSON.stringify({ error: 'DB read failed' }) };
  }
};