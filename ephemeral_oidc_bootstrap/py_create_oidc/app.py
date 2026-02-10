import boto3
import json

def lambda_handler(event, context):
    client = boto3.client('iam')
    account_id = client.get_caller_identity()['Account']

# Generiere die ARN des OIDC Providers basierend auf der Account ID
    
    oidc_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

    # Die ARN des OIDC-Providers, die wir benötigen
    oidc_provider_arn = event['ResourceProperties'].get('OidcProviderArn', oidc_provider_arn)
    # oidc_provider_arn = event['ResourceProperties']['OidcProviderArn']

    try:
        # Prüfe, ob der OIDC-Provider existiert
        response = client.list_openid_connect_providers()
        exists = any(provider_arn == oidc_provider_arn for provider_arn in response['OpenIDConnectProviderList'])
        
        if exists:
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': 'OidcProviderExists'  # Oder eine andere ID, die dir gefällt
            }
        else:
            # OIDC-Provider existiert nicht, also erstellen wir ihn
            response = client.create_openid_connect_provider(
                Url='https://token.actions.githubusercontent.com',
                ClientIdList=['sts.amazonaws.com'],
                ThumbprintList=['6938fd4d98bab03faadb97b34396831e3780aea1']
            )
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': response['OpenIDConnectProviderArn']
            }
    except Exception as e:
        return {
            'Status': 'FAILED',
            'Reason': str(e)
        }
