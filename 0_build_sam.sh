rm -rf .aws-sam/build
# Remove-Item -Recurse -Force .aws-sam\build
sam build
sam deploy --force-upload