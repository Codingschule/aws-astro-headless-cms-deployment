import boto3
import logging
import json
import requests

iam_client = boto3.client('iam')

def send_response(status, reason, physical_resource_id, data, event):
    """ Send response to CloudFormation """
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
    # Hole die OIDC URL und die Option, ob gelöscht werden soll
    oidc_url = event.get("OidcUrl", "https://token.actions.githubusercontent.com")
    delete_oidc = event.get("DeleteOidcWithCustomResource", False)  # Standardwert ist False
    stack_id = event['StackId']  # StackId aus dem Event

    # Handle Create and Update (beides ist identisch)
    if event['RequestType'] in ['Create', 'Update']:
        try:
            # Prüfen, ob OIDC Provider erstellt werden muss
            try:
                # Versuche, den OIDC Provider zu erstellen
                response = iam_client.create_open_id_connect_provider(
                    Url=oidc_url,
                    ClientIDList=['sts.amazonaws.com'],
                    ThumbprintList=['6938fd4d98bab03faadb97b34396831e3780aea1'],
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
        # Prüfen, ob der OIDC-Provider gelöscht werden soll
        if delete_oidc and event['StackId'] == stack_id:
            try:
                # Lösche den OIDC Provider, wenn er existiert
                response = iam_client.delete_open_id_connect_provider(
                    OpenIDConnectProviderArn=oidc_url
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
