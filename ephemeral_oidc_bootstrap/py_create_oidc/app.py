import boto3
import json

def lambda_handler(event, context):
    # Verwende den sts Client, um die Account-ID zu bekommen
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']

    # Generiere die ARN des OIDC Providers basierend auf der Account ID
    oidc_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

    # Versuche, 'ResourceProperties' aus dem Event zu holen
    resource_properties = event.get('ResourceProperties', {})
    
    # Hole die OIDC Provider ARN, falls verfügbar, ansonsten die generierte ARN verwenden
    oidc_provider_arn = resource_properties.get('OidcProviderArn', oidc_provider_arn)

    try:
        # IAM Client zum Erstellen und Abfragen von OIDC Providern
        client = boto3.client('iam')

        # Wenn der Provider existiert, überspringen. Andernfalls erstellen.
        try:
            response = client.list_openid_connect_providers()
            exists = any(provider_arn == oidc_provider_arn for provider_arn in response['OpenIDConnectProviderList'])
        except client.exceptions.NoSuchEntityException:
            exists = False

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
