import boto3
import logging
import json
import requests
from urllib.parse import urlparse

iam_client = boto3.client('iam')
sts_client = boto3.client('sts')
tagging_client = boto3.client('resourcegroupstaggingapi')  # Verwende den richtigen Tagging-Client

logging.basicConfig(level=logging.warning)

logging.error("LOGGING WORKS logging.error ######################## START #################################")
logging.critical("LOGGING WORKS logging.critical")
logging.warning("LOGGING WORKS logging.warning")

logging.debug("LOGGING WORKS logging.debug") # IGNORED BY CLOUDWATCH
logging.info("LOGGING WORKS logging.info") # IGNORED BY CLOUDWATCH

DEBUG_NO_RESPONSE = False
SEPERATOR = "+"

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


    if DEBUG_NO_RESPONSE:
        logging.warning(f"####[DEBUG_NO_RESPONSE]#### \n response_body={response_body} \n event:{event}")
        if status == "FAILED":
            raise Exception(f"{response_body} \n event:{event}")
        else:
            return response_body
    else:
        try:
            r = requests.put(response_url, json=response_body)
            logging.warning(f"CloudFormation response sent: {r.status_code}")
        except Exception as e:
            txt = f"Failed to send response to CloudFormation: response_body={response_body}  \n  r={r} \n event:{event}"
            logging.error(txt)
            raise Exception(txt)


def get_stack_name_from_arn(stack_arn):
    """
    Extracts the stack name from the ARN.
    """
    return stack_arn.split('/')[1]  # Extracting the stack name from the ARN

def create_or_delete_oidc_provider(oidc_url, oidc_client_id, oidc_thumb_print, stack_id, stack_name, delete_oidc, event):
    """
    Manages the creation or deletion of the OIDC provider.
    """
    logging.warning(f"create_or_delete_oidc_provider() start")
                
    account_id = sts_client.get_caller_identity()['Account']

    # Verwende urlparse, um die Domain zuverlässig zu extrahieren
    parsed_url = urlparse(oidc_url)
    oidc_domain = parsed_url.netloc

    # Erstelle den OIDC ARN dynamisch
    oidc_arn = f"arn:aws:iam::{account_id}:oidc-provider/{oidc_domain}"

    logging.warning(f"create_or_delete_oidc_provider() try1")
    logging.warning(f"create_or_delete_oidc_provider() event['RequestType']={event['RequestType']}")
    try:
        if event['RequestType'] in ['Create', 'Update']:
            logging.warning(f"create_or_delete_oidc_provider() try2")
            try:
                response = iam_client.create_open_id_connect_provider(
                    Url=oidc_url,
                    ClientIDList=[oidc_client_id],
                    ThumbprintList=[oidc_thumb_print],
                    Tags=[
                        {'Key': 'Created-By-Stack', 'Value': event['StackId']},
                        {'Key': 'Used-By-Stacks',   'Value': stack_name}
                        ]
                )
                return response, oidc_arn

            except iam_client.exceptions.EntityAlreadyExistsException:
                logging.warning(f"OIDC Provider already exists: {oidc_url}")
                return {'OpenIDConnectProviderArn': oidc_arn}, oidc_arn

        elif event['RequestType'] == 'Delete':
            logging.warning(f"create_or_delete_oidc_provider() delete")
            if delete_oidc:
                logging.warning(f"create_or_delete_oidc_provider() delete_oidc={delete_oidc}")
                response = iam_client.delete_open_id_connect_provider(OpenIDConnectProviderArn=oidc_arn)
                return response, oidc_arn
            else:
                logging.warning(f"create_or_delete_oidc_provider() just kidding - not deleting...")
                return {}, oidc_arn

        else:
            logging.warning(f"create_or_delete_oidc_provider() else")
            logging.error(f"unknown Event Requesttype! Event: {event}")
            send_response("FAILED", f"Error: {str(e)}", oidc_url, {"Error": str(e)}, event)
            raise e

        logging.warning(f"create_or_delete_oidc_provider() EndIf")

    except Exception as e:
        logging.error(f"Error creating or deleting OIDC provider: {str(e)}")
        send_response("FAILED", f"Error: {str(e)}", oidc_url, {"Error": str(e)}, event)
        raise e

def update_tags_for_oidc_provider(oidc_arn, stack_name, event):
    """
    Update or remove the tags for the OIDC provider using resourcegroupstaggingapi
    """

    logging.warning(f"update_tags_for_oidc_provider() try")
    try:
        # Hole den 'Used-By-Stacks' Tag und aktualisiere ihn sicher
        response = tagging_client.get_resources(TagFilters=[{'Key': 'Used-By-Stacks'}])
        logging.warning(f"update_tags_for_oidc_provider() response {response}")

        # all_tags = response['ResourceTagMappingList'][0]['Tags']
        # logging.warning(f"update_tags_for_oidc_provider() all_tags {all_tags}")
        # Sicherstellen, dass wir einen gültigen Tagwert haben, bevor wir 'split()' verwenden
        tag_value = response['ResourceTagMappingList'][0]['Tags'][0].get('Value', '') if len(response['ResourceTagMappingList']) > 0 else ""
        logging.warning(f"update_tags_for_oidc_provider() tag_value={tag_value}")

        set_existing_stacks = set(tag_value.split(SEPERATOR)) if tag_value else set()
        logging.warning(f"update_tags_for_oidc_provider() set_existing_stacks={set_existing_stacks}")
        if event['RequestType'] in ['Create', 'Update']:
            set_existing_stacks.add(stack_name)

        elif event['RequestType'] == 'Delete' and stack_name in set_existing_stacks:
            set_existing_stacks.remove(stack_name)

        # Sicherstellen, dass der 'Used-By-Stacks' Tag korrekt erstellt oder aktualisiert wird
        s_new_used_stacks = SEPERATOR.join(set_existing_stacks).strip()
        logging.warning(f"update_tags_for_oidc_provider() s_new_used_stacks={s_new_used_stacks}")

        # Tag setzen, wenn der resultierende String nicht leer ist
        if s_new_used_stacks != "":  # Stelle sicher, dass der String nicht leer ist
            logging.warning(f"update_tags_for_oidc_provider() tag_resources")
            r2 = tagging_client.tag_resources(
                ResourceARNList=[oidc_arn],
                Tags={'Used-By-Stacks': s_new_used_stacks}
            )
        else:
            logging.warning(f"update_tags_for_oidc_provider() untag_resources")
            r2 = tagging_client.untag_resources(
                ResourceARNList=[oidc_arn],
                TagKeys=['Used-By-Stacks']
            )

        logging.warning(f"update_tags_for_oidc_provider() r2={r2}")
        # Hier wird überprüft, ob r2 erfolgreich war (je nachdem, was von der API zurückgegeben wird)
        # if not r2.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
        if not r2.get('StatusCode', r2['ResponseMetadata']['HTTPStatusCode']) == 200:
            raise Exception(f"Failed to update tags for OIDC provider. Response: {r2}")

        logging.warning(f"OK Updated set_existing_stacks: {s_new_used_stacks}")

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

    manage_tags = False if str(event['ResourceProperties'].get("ManageTags", True)).lower() in ["false", "1"] else True

    global DEBUG_NO_RESPONSE
    DEBUG_NO_RESPONSE = True if str(event['ResourceProperties'].get("DEBUG_NO_RESPONSE", False)).lower().strip() in ["true", "1"] else False


    logging.warning(f"EventType: {event['RequestType']} - StackId: {stack_id} - StackName: {stack_name} - DeleteOidcWithCustomResource: {delete_oidc}")
    logging.warning(f"Event: {event}")

    logging.warning(f"lambda_handler() try")
    try:
        logging.warning(f"lambda_handler() create_or_delete_oidc_provider")
        provider_response, oidc_arn = create_or_delete_oidc_provider(
            oidc_url, oidc_client_id, oidc_thumb_print, stack_id, stack_name, delete_oidc, event
        )

        if manage_tags:
            if delete_oidc and event['RequestType'] == "Delete":
                logging.warning(f"lambda_handler() SKIPPING: update_tags_for_oidc_provider for DELETED object")
            else:
                logging.warning(f"lambda_handler() update_tags_for_oidc_provider")
                update_tags_for_oidc_provider(oidc_arn, stack_name, event)

        logging.warning(f"lambda_handler() send_response")
        response = send_response(
            "SUCCESS",
            f"OIDC Provider {event['RequestType']} successfully processed.",
            provider_response['OpenIDConnectProviderArn'] if 'OpenIDConnectProviderArn' in provider_response else oidc_arn,
            {"OpenIDConnectProviderArn": provider_response['OpenIDConnectProviderArn'] if 'OpenIDConnectProviderArn' in provider_response else oidc_arn},
            event
        )

    except Exception as e:
        logging.warning(f"lambda_handler() except")
        send_response("FAILED", f"Error: {str(e)}", oidc_url, {"Error": str(e)}, event)
        raise e
    
    logging.error("LOGGING WORKS logging.error -------------------------------- END --------------------------------")
    return response
