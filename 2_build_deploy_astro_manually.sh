cd frontend
npm install
npm run build
cd ..
aws s3 sync ./frontend/dist/ s3://cs-itp-ssg-cd-sam-frontend-astro207b-us-east-1-867405369211 --delete --profile=myawsprofile
