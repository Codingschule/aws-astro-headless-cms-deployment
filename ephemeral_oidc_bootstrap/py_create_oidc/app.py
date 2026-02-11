import boto3
import logging
import json
import requests

# IAM-Client initialisieren
iam_client = boto3.client('iam')

def send_response(status, reason, physical_resource_id, data, event):
    """ Send response to CloudFormation """
    response_body = {
        'Status': status,
        'Reason': reason,
        'PhysicalResourceId': physical_resource_id,
        'Data': data
    }
    response_url = event['ResponseURL']  # Die ResponseURL, die von CloudFormation übergeben wird

    try:
        response = requests.put(response_url, json=response_body)
        logging.info(f"Response sent to CloudFormation: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to send response to CloudFormation: {str(e)}")

def lambda_handler(event, context):
    # Die URL des OIDC Providers (z. B. GitHub Actions)
    oidc_url = event.get("OidcUrl", "https://token.actions.githubusercontent.com")
    
    try:
        # Erstelle den OIDC Provider
        response = iam_client.create_open_id_connect_provider(
            Url=oidc_url,
            ClientIDList=['sts.amazonaws.com'],
            ThumbprintList=['6938fd4d98bab03faadb97b34396831e3780aea1'],
            Tags=[{'Key': 'Created-By', 'Value': 'Lambda'}]
        )
        
        # Erfolgreiche Antwort zurückgeben
        send_response(
            'SUCCESS',  # Benachrichtige CloudFormation über den Erfolg
            'OIDC Provider successfully created',
            response['OpenIDConnectProviderArn'],  # Die ARN des Providers
            {
                'OpenIDConnectProviderArn': response['OpenIDConnectProviderArn']
            },
            event
        )

    except iam_client.exceptions.EntityAlreadyExistsException as e:
        # Fehler: OIDC Provider existiert bereits
        logging.error(f"Error: OIDC Provider already exists: {str(e)}")
        
        send_response(
            'SUCCESS',  # Erfolgreich, aber der Provider existiert bereits
            f"OIDC Provider with URL {oidc_url} already exists.",
            oidc_url,  # Verwende die URL als eindeutigen Bezeichner
            {
                'Message': f"OIDC Provider already exists",
                'OidcProviderArn': oidc_url
            },
            event
        )

    except Exception as e:
        # Alle anderen Fehler
        logging.error(f"Error: {str(e)}")
        
        send_response(
            'FAILED',  # Fehlerstatus
            str(e),
            oidc_url,  # Verwende die URL als Identifikator
            {
                'Error': str(e)
            },
            event
        )
