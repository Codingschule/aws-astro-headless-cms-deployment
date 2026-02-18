# Tickets
Features to implement

## AWS Cloud Landing Page (done)
Old Version: Use CloudFormation for provisioning, save a static website into an S3 bucket

## Static Web Deployment on AWS with CI/CD Foundations (done)
Add CloudFront CDN, Https, Caching, make S3 Bucket private; Implement a GitHub Actions Build Pipeline using AccessKeys or STS.

## AWS Lambda Guestbook API
Implement Serverless Guestbook with API-Gateway, Lambda, DynamoDB Table.
Please be aware, the Tickets were created with limited knowledge how AWS SAM works and what it includes, Currently cross-Ticket progress since aws SAM cli serves not only Provisioning but also Building and Deploying.

1. 001-[Infra] - Provision Serverless Resources (CloudFormation/SAM)
   * **Objective:** Extend your existing CloudFormation template to provision a modular guestbook backend. You will leverage **AWS SAM (Serverless Application Model)** resources to separate the application logic (API & Database) from your hosting layer (S3/CloudFront).
   * **Task Description:** Instead of creating a new file, integrate the following resources into your current template. Since you already have the `Transform: AWS::Serverless-2016-10-31` header at the top, you can use the simplified `AWS::Serverless` resource types directly.
   * **Acceptance Criteria:**
   1. **Database:** Define a `AWS::Serverless::SimpleTable` (DynamoDB) named `GuestbookEntries` with a Partition Key `id` (Type: String).
   2. **Serverless Logic:** Define an `AWS::Serverless::Function` for the backend logic:
      * **Runtime:** Node.js 24.x.
      * **Code:** For now, use `InlineCode` or point `CodeUri` to a folder containing your handler.
   3. **API Gateway:** Configure an `Events` source of type `Api` to expose a `/guestbook` endpoint. It must support `GET`, `POST`, and `OPTIONS` (Note: Using `Method: any` is the simplest way to handle this).
   4. **Security (IAM):** Grant the Lambda permission to interact with the database using the SAM `Policies` attribute. Use the `DynamoDBCrudPolicy` scoped specifically to your new table.
   5. **Outputs:** Export the following values so they can be used by the frontend:
      * `GuestbookApiEndpoint`: The full URL to your API.
      * `GuestbookTableName`: The actual name of the DynamoDB table.
      * **Optional / Pro-Tip:** Try to use a `!Sub` (Substitute) function in the Outputs to construct the API URL dynamically using the `${ServerlessRestApi}` reference that SAM creates automatically.

2. 002-[DevOps] - Lambda Artifact Management & Deployment Pipeline
   * Establish a process to package the Lambda source code and make it available for CloudFormation deployments.
   * **Acceptance Criteria:**
     * Identify or create an **S3 Bucket** to host Lambda deployment packages (`.zip` files).
     * Create a deployment script (e.g., `deploy-backend.sh`) or update the existing CI/CD pipeline to:
       1. Zip the `lambda/` directory.
       2. Upload `guestbook.zip` to the S3 bucket.
       3. Run the CloudFormation deploy command using the uploaded S3 key.
   * Ensure the Lambda environment variable `TABLE_NAME` is dynamically injected from the CloudFormation stack.

3. 003-[Security] - Enable CORS & API Gateway Configuration
Ensure the Astro frontend (running on a different domain/CDN) can securely communicate with the API Gateway.
   * **Acceptance Criteria:**
     * Configure **CORS** on the API Gateway (Allow-Origin: `*` or the specific CloudFront URL).
     * Ensure the `OPTIONS` method is correctly handled (Mock integration or Lambda Proxy) to allow browser pre-flight requests.
     * Enable **CloudWatch Logs** for the API Gateway to monitor incoming traffic and troubleshoot failed submissions.

1. 004-[DevOps] - Automate API Endpoint Integration for Frontend Build
   * To avoid manual configuration and "configuration drift," we will automate the handover of the API Gateway URL. The frontend build process should dynamically fetch the endpoint from AWS instead of relying on manually set GitHub Variables.
   * **Acceptance Criteria:**
     * **AWS Output:** Ensure the CloudFormation stack `120_serverless_guestbook` exports the `GuestbookApiEndpoint` in the `Outputs` section.
     * **CI/CD Integration:** Update `.github/workflows/deploy.yml` to include a step that queries the CloudFormation Output using the AWS CLI.
     * **Environment Injection:** Map the fetched output to the environment variable `VITE_PUBLIC_GUESTBOOK_API_URL` so it is available during the `npm run build` (Astro) step.
     * **Local Development:** Add a note to `README.md` explaining how developers can fetch the current API URL for their local `.env` (e.g., via `aws cloudformation describe-stacks ...`).

2. 005-[Frontend/Logic] - Implement Dynamic Guestbook with Alpine.js
   * Build the guestbook frontend using **Alpine.js** for reactive data fetching and form handling. This ensures a "live" feel where comments are loaded and displayed without a full page rebuild.
   * **Acceptance Criteria:**
     1. Alpine.js Integration:
        * Add Alpine.js to the project (either via Astro integration `npx astro add alpinejs` or a simple script tag).
     2. Frontend - Reactive Guestbook Logic (**`x-data`**):
        * Create an Alpine.js component that manages the state: `entries` (array), `isLoading` (boolean), and `errorMessage` (string).
        * Implement an `init()` function to automatically fetch comments from the API Gateway on page load.
     3. Frontend - Dynamic List Rendering (**`x-for`**):
        * Use `x-for` to iterate through the fetched testimonials.
        * Display a **loading spinner** or skeleton using `x-show="isLoading"`.
        * Show the list once `isLoading` is false.
     4. Frontend - Form Submission:
        * Use `x-model` for two-way binding on the form inputs (name, message).
        * Handle form submission with `@submit.prevent`.
        * **Immediate Update:** After a successful POST request, push the new entry directly into the local `entries` array so it appears instantly for the user.
