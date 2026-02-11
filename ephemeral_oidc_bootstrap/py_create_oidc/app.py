import boto3
import logging
import json

# IAM-Client initialisieren
iam_client = boto3.client('iam')

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
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'OIDC Provider erfolgreich erstellt!',
                'OpenIDConnectProviderArn': response['OpenIDConnectProviderArn']
            })
        }

    except iam_client.exceptions.EntityAlreadyExistsException as e:
        # Fehler: OIDC Provider existiert bereits
        logging.error(f"Error: OIDC Provider already exists: {str(e)}")
        
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': f"OIDC Provider with URL {oidc_url} already exists.",
                'error': str(e)
            })
        }

    except Exception as e:
        # Alle anderen Fehler
        logging.error(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
