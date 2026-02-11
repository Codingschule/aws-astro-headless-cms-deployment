import boto3
import logging
import json
import requests

iam_client = boto3.client('iam')

def send_response(status, reason, physical_resource_id, data, event):
    response_body = {
        "Status": status,
        "Reason": reason,
        "PhysicalResourceId": physical_resource_id,
        "StackId": event['StackId'],               # Pflicht
        "RequestId": event['RequestId'],           # Pflicht
        "LogicalResourceId": event['LogicalResourceId'],  # Pflicht
        "Data": data
    }
    response_url = event['ResponseURL']

    try:
        r = requests.put(response_url, json=response_body)
        logging.info(f"CloudFormation response sent: {r.status_code}")
    except Exception as e:
        logging.error(f"Failed to send CloudFormation response: {str(e)}")


def lambda_handler(event, context):
    oidc_url = event.get("OidcUrl", "https://token.actions.githubusercontent.com")

    try:
        response = iam_client.create_open_id_connect_provider(
            Url=oidc_url,
            ClientIDList=['sts.amazonaws.com'],
            ThumbprintList=['6938fd4d98bab03faadb97b34396831e3780aea1'],
            Tags=[{'Key': 'Created-By-Stack', 'Value': event['StackId']}],
            Tags=[{'Key': 'Created-By', 'Value': 'Lambda'}]
        )

        send_response(
            "SUCCESS",
            "OIDC Provider successfully created",
            response['OpenIDConnectProviderArn'],
            {"OpenIDConnectProviderArn": response['OpenIDConnectProviderArn']},
            event
        )

    except iam_client.exceptions.EntityAlreadyExistsException:
        send_response(
            "SUCCESS",
            f"OIDC Provider already exists: {oidc_url}",
            oidc_url,
            {"Message": "Already exists", "OidcUrl": oidc_url},
            event
        )

    except Exception as e:
        logging.error(str(e))
        send_response(
            "FAILED",
            str(e),
            oidc_url,
            {"Error": str(e)},
            event
        )
