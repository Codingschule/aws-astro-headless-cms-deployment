import boto3
import logging
import json
import requests
from urllib.parse import urlparse

iam_client = boto3.client('iam')
sts_client = boto3.client('sts')
tagging_client = boto3.client('resourcegroupstaggingapi')

def send_response(status, reason, physical_resource_id, data, event):
    """
    Sends a response to CloudFormation after processing the custom resource request.
    """
    response_body = {
        "Status": status,
        "Reason": reason,
        "PhysicalResourceId": physical_resource_id,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": data
    }
    response_url = event['ResponseURL']

    try:
        r = requests.put(response_url, json=response_body)
        logging.info(f"CloudFormation response sent: {r.status_code}")
    except Exception as e:
        logging.error(f"Failed to send response to CloudFormation: {str(e)}")

def get_stack_name_from_arn(stack_arn):
    """
    Extracts the stack name from the ARN.
    """
    return stack_arn.split('/')[1]  # Extracting the stack name from the ARN

def create_or_delete_oidc_provider(oidc_url, oidc_client_id, oidc_thumb_print, stack_id, stack_name, delete_oidc, event):
    """
    Manages the creation or deletion of the OIDC provider.
    """
    account_id = sts_client.get_caller_identity()['Account']

    # Verwende urlparse, um die Domain zuverlässig zu extrahieren
    parsed_url = urlparse(oidc_url)
    oidc_domain = parsed_url.netloc

    # Erstelle den OIDC ARN dynamisch
    oidc_arn = f"arn:aws:iam::{account_id}:oidc-provider/{oidc_domain}"

    try:
        if event['RequestType'] in ['Create', 'Update']:
            try:
                response = iam_client.create_open_id_connect_provider(
                    Url=oidc_url,
                    ClientIDList=[oidc_client_id],
                    ThumbprintList=[oidc_thumb_print],
                    Tags=[{'Key': 'Created-By-Stack', 'Value': event['StackId']}, {'Key': 'Created-By', 'Value': 'Lambda'}]
                )
                return response, oidc_arn

            except iam_client.exceptions.EntityAlreadyExistsException:
                logging.info(f"OIDC Provider already exists: {oidc_url}")
                return {'OpenIDConnectProviderArn': oidc_arn}, oidc_arn

        elif event['RequestType'] == 'Delete':
            if delete_oidc:
                response = iam_client.delete_open_id_connect_provider(OpenIDConnectProviderArn=oidc_arn)
                return response, oidc_arn

    except Exception as e:
        logging.error(f"Error creating or deleting OIDC provider: {str(e)}")
        send_response("FAILED", f"Error: {str(e)}", oidc_url, {"Error": str(e)}, event)
        raise e

def update_tags_for_oidc_provider(oidc_arn, stack_name, event, delete_oidc):
    """
    Update or remove the tags for the OIDC provider using resourcegroupstaggingapi
    """
    try:
        # Tag für 'Used-By-Stack' hinzufügen oder entfernen
        if event['RequestType'] in ['Create', 'Update']:
            tagging_client.tag_resources(
                ResourceARNList=[oidc_arn],
                Tags={'Used-By-Stack-' + stack_name: event['StackId']}
            )

        elif event['RequestType'] == 'Delete' and delete_oidc:
            tagging_client.untag_resources(
                ResourceARNList=[oidc_arn],
                TagKeys=['Used-By-Stack-' + stack_name]
            )

        # Abrufen der 'Used-By-Stacks' Tags
        used_by_stacks_tag = tagging_client.get_resources(TagFilters=[{'Key': 'Used-By-Stacks'}]).get('ResourceTagMappingList', [])
        
        # Sicherstellen, dass Tags existieren, bevor wir sie verarbeiten
        existing_stacks = set()
        for tag_mapping in used_by_stacks_tag:
            for tag in tag_mapping.get('Tags', []):
                if tag.get('Key') == 'Used-By-Stacks' and tag.get('Value'):
                    existing_stacks.add(tag['Value'])

        # Debug-Log, um zu sehen, welche Tags wir haben
        logging.debug(f"Existing 'Used-By-Stacks' tags: {existing_stacks}")

        # Stacknamen für Create/Update hinzufügen
        if event['RequestType'] in ['Create', 'Update']:
            existing_stacks.add(stack_name)

        # Für Delete: Stacknamen entfernen
        elif event['RequestType'] == 'Delete' and delete_oidc:
            existing_stacks.discard(stack_name)

        # Setze den neuen Wert des 'Used-By-Stacks' Tags
        new_used_by_stacks = ",".join(sorted(existing_stacks))

        tagging_client.tag_resources(
            ResourceARNList=[oidc_arn],
            Tags={'Used-By-Stacks': new_used_by_stacks}
        )

    except Exception as e:
        logging.error(f"Error updating tags for OIDC provider: {str(e)}")
        send_response("FAILED", f"Error: {str(e)}", oidc_arn, {"Error": str(e)}, event)
        raise e

def lambda_handler(event, context):
    """
    Lambda handler function to manage the creation and deletion of an OpenID Connect (OIDC) provider.
    """
    oidc_url = event['ResourceProperties'].get("OidcProviderUrl", "https://token.actions.githubusercontent.com")
    oidc_client_id = event['ResourceProperties'].get("OidcClientId", "sts.amazonaws.com")
    oidc_thumb_print = event['ResourceProperties'].get("OidcThumbPrint", "6938fd4d98bab03faadb97b34396831e3780aea1")
    
    stack_id = event['StackId']
    stack_name = get_stack_name_from_arn(stack_id)
    
    delete_oidc = True if str(event['ResourceProperties'].get("DeleteOidcWithCustomResource", False)).lower() in ["true", "1"] else False

    logging.info(f"EventType: {event['RequestType']} - StackId: {stack_id} - StackName: {stack_name} - DeleteOidcWithCustomResource: {delete_oidc}")

    try:
        provider_response, oidc_arn = create_or_delete_oidc_provider(
            oidc_url, oidc_client_id, oidc_thumb_print, stack_id, stack_name, delete_oidc, event
        )

        update_tags_for_oidc_provider(oidc_arn, stack_name, event, delete_oidc)

        send_response(
            "SUCCESS",
            f"OIDC Provider {event['RequestType']} successfully processed.",
            provider_response['OpenIDConnectProviderArn'] if 'OpenIDConnectProviderArn' in provider_response else oidc_arn,
            {"OpenIDConnectProviderArn": provider_response['OpenIDConnectProviderArn'] if 'OpenIDConnectProviderArn' in provider_response else oidc_arn},
            event
        )

    except Exception as e:
        send_response("FAILED", f"Error: {str(e)}", oidc_url, {"Error": str(e)}, event)
        raise e
