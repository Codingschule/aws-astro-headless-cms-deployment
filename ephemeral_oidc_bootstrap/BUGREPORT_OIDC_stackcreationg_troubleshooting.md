# BUGREPORT

# oidc bootstrapping project - background
The "epheremal_oidc_bootstrap" SAM Project aims to create an extra stack, cointaining a python lambda function "py_create_oidc/app.py" which shall create an OIDC provider for github (if not yet exists).

```yml
  OidcProviderCheckLambda:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.lambda_handler
#      Role: !Ref OidcProviderCreationRole
      Role: !GetAtt OidcProviderCreationRole.Arn
      Runtime: python3.13
      CodeUri: ./py_create_oidc
      # Code:
      #   S3Bucket: myBucket
      #   S3Key: myLambdaCode.zip
      Timeout: 10 # seconds
```


The SAM template than runs this function as part of stack deploying.

```yml
  RunMyLambdaOidcProviderCheck: ##
    Type: Custom::OidcProviderCheck
    Properties:
      ServiceToken: !GetAtt OidcProviderCheckLambda.Arn
      OidcProviderArn: !Sub "arn:aws:iam::${AWS::AccountId}:oidc-provider/token.actions.githubusercontent.com"
      Timeout: 10 # seconds
#      MemorySize: 128
```

- In the cloudfdormation stack overview, the stack is than endlessly in the state "CREATING"
- The Ressource RunMyLambdaOidcProviderCheck trying to run the python Script stays endlessly in the state CREATING
  - even tho timeout was set to 5 seconds for the Custom Resource
- The Stack Deletion Fails for several hours DELETE_IN_PROGRESS
- The Stack can be deleted after several hour when trying again
