import boto3
import json

iam = boto3.client('iam')

def lambda_handler(event, context):
    # 1) OIDC‑URL (z.B. GitHub Actions)
    oidc = event.get("Url", "https://token.actions.githubusercontent.com")

    # 2) API‑Aufruf zur Erstellung des Providers
    response = iam.create_open_id_connect_provider(
        Url=oidc,
        ClientIDList=['sts.amazonaws.com'],
        ThumbprintList=['9e99a48a9960b14926bb7f3b02e22da2b0ab7280'],
        Tags=[{'Key': 'Created-By', 'Value': 'Lambda'}]
    )

    return {
        "OpenIDConnectProviderArn": response['OpenIDConnectProviderArn']
    }
