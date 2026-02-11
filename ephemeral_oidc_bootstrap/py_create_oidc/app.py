import boto3
import logging
import json
import requests
from urllib.parse import urlparse

iam_client = boto3.client('iam')
sts_client = boto3.client('sts')

def send_response(status, reason, physical_resource_id, data, event):
    """
    Sends a response to CloudFormation after processing the custom resource request.
    
    Args:
        status (str): The status of the operation ('SUCCESS' or 'FAILED').
        reason (str): A message explaining the result of the operation.
        physical_resource_id (str): The unique identifier for the resource, typically ARN or URL.
        data (dict): Additional data to include in the response to CloudFormation.
        event (dict): The CloudFormation event object, contains details about the request.
    
    Returns:
        None: Sends a response to CloudFormation using a PUT request.
    """
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
        logging.error(f"Failed to send response to CloudFormation: {str(e)}")


def lambda_handler(event, context):
    """
    Lambda handler function to manage the creation and deletion of an OpenID Connect (OIDC) provider.
    
    The function is triggered by a CloudFormation custom resource. It can handle:
        1. The creation of a new OIDC provider using AWS IAM.
        2. Deletion of an existing OIDC provider if certain conditions are met.
    
    Args:
        event (dict): The CloudFormation event that triggers the Lambda function.
        context (LambdaContext): The runtime context of the Lambda function.
    
    Returns:
        dict: The response sent back to CloudFormation, indicating success or failure.
        
    CloudFormation Custom Resource Parameters:
        - OidcProviderUrl (str): The URL of the OIDC provider (default: "https://token.actions.githubusercontent.com").
        - OidcClientId (str): The client ID to associate with the provider (default: "sts.amazonaws.com").
        - OidcThumbPrint (str): The thumbprint of the OIDC provider's SSL certificate (default: "6938fd4d98bab03faadb97b34396831e3780aea1").
        - OidcProviderArn (str): The ARN of the OIDC provider (dynamically constructed if not provided).
        - DeleteOidcWithCustomResource (bool): Whether to delete the OIDC provider on stack deletion (default: False).
        - Timeout (int): Timeout in seconds for the operation (default: 3).
    """
    # Hole die OIDC URL aus den ResourceProperties
    oidc_url = event['ResourceProperties'].get("OidcProviderUrl", "https://token.actions.githubusercontent.com")
    oidc_client_id = event['ResourceProperties'].get("OidcClientId", "sts.amazonaws.com")
    oidc_thumb_print = event['ResourceProperties'].get("OidcThumbPrint", "6938fd4d98bab03faadb97b34396831e3780aea1")
    
    # Hole die AWS Account ID durch sts
    account_id = sts_client.get_caller_identity()['Account']
    
    # Verwende urlparse, um die Domain zuverlässig zu extrahieren
    parsed_url = urlparse(oidc_url)
    oidc_domain = parsed_url.netloc  # Extrahiert den Domain-Teil ohne Protokoll und Slash

    # Erstelle den OIDC ARN dynamisch
    oidc_arn = f"arn:aws:iam::{account_id}:oidc-provider/{oidc_domain}"
    
    # Hole den benutzerdefinierten Parameter DeleteOidcWithCustomResource
    delete_oidc = event['ResourceProperties'].get("DeleteOidcWithCustomResource", False)  # Standardwert ist False
    stack_id = event['StackId']  # StackId aus dem Event

    logging.info(f"DeleteOidcWithCustomResource: {delete_oidc}, StackId: {stack_id}, EventType: {event['RequestType']}")

    # Handle Create and Update (beides ist identisch)
    if event['RequestType'] in ['Create', 'Update']:
        try:
            # Prüfen, ob OIDC Provider erstellt werden muss
            try:
                # Versuche, den OIDC Provider zu erstellen
                response = iam_client.create_open_id_connect_provider(
                    Url=oidc_url,
                    ClientIDList=[oidc_client_id],
                    ThumbprintList=[oidc_thumb_print],
                    Tags=[
                        {'Key': 'Created-By-Stack', 'Value': event['StackId']},  # Füge StackId als Tag hinzu
                        {'Key': 'Created-By', 'Value': 'Lambda'}
                    ]
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

    # Handle Delete
    elif event['RequestType'] == 'Delete':
        logging.info("Delete request received.")

        # Prüfen, ob der OIDC-Provider gelöscht werden soll
        if delete_oidc and event['StackId'] == stack_id:
            try:
                # Lösche den OIDC Provider, wenn er existiert
                response = iam_client.delete_open_id_connect_provider(
                    OpenIDConnectProviderArn=oidc_arn
                )
                send_response(
                    "SUCCESS",
                    f"OIDC Provider with URL {oidc_url} successfully deleted.",
                    oidc_url,
                    {"Message": "OIDC Provider deleted"},
                    event
                )
            except Exception as e:
                logging.error(f"Error deleting OIDC provider: {str(e)}")
                send_response(
                    "FAILED",
                    f"Error deleting OIDC provider: {str(e)}",
                    oidc_url,
                    {"Error": str(e)},
                    event
                )
        else:
            send_response(
                "SUCCESS",
                "Delete request ignored - conditions not met",
                oidc_url,
                {"Message": "OIDC provider was not deleted, conditions not met."},
                event
            )
