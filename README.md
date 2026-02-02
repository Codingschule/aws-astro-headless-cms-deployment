# aws-astro-headless-cms-deployment
deployment part of website
This readme will mainly serve as documentation and optionally as guided landing page for this project.

You can clone this repo for a template of deploying a SSG website on AWS.
Or you can use it as walkthrough to build your own.

## prerequisites 

- install NodeJS
- install aws cli
- install git
- some code editor (we use vscode, and plugins aws toolkit, git, astro)
- be able to run a console command on cmd, powershell, bash
  - beware: 
    - if you run wsl-bash (default), it might not find your windows git/npm/nodejs.
    - git for windows comes with a windows-native bash that can run your windows apps.

## directory structure

- frontend ontains the astro static site generator (ssg) project
- cloudformation for provisioning AWS infrastructure
- doc example files

## scafffold Astro (if not cloning this repo)

- clone or create new git repo
- choose a [theme][themes] (we go with "blog" and have a [patchfile][patchfile] for optionalle integrating strapi)
- cd into repo dir
- `npm create astro@latest -- --template blog frontend`
  - will generate an [astro] project
  - in case npm depency installation fails, close your loud sync, give your virus scanner 1-2 minutes (it probably checks npm_nodes) and run:
    - cd frontend
    - npm install

### build astro and run local webserver

You can now build html files from your astro project
- cd frontend

spin up an auto-refreshing **dev**eloper webserver, reflecting the current state of your src:
- `npm run dev` this will...
- spin up webserver on http://localhost:4321/
- ~~will open browser~~

finally, build your static website
- `npm run build`
- will store into "dist", which is ignored through [gitignore]
- in our setup, we will not store the ou tput files in the repo but sync them manually OR generate it remote using a pipeline.

start a static webserver for the "dist" directory, ignoring src changes:
- `npm run preview`

---

## strapi (out of scope of this project)

Whilst this project focuses on the SSG part, here are some steps to integrate strapi

### strapi quickstart without cloud

This is quick & dirty - you might not want to include [strapi] in the astro repository...

- change dir to project root
- npx dreate-strapi-app@latest backend-strapi
- cd backend-strapi
- npm run dev
  - alias for npm strapi develop
- a webbrowser should open, register and log in
  - mark draft posts and publish them to get some content

## integrate strapi into astro

Thats it. If you want Astro to query posts from [strapi], heres the local setup.
It does not follo the [Integration Guide][integrate] since we do not use its SaaS here.
- cd frontend-astro
- npm create astro@latest -- --template blog frontend-astro
  - IF NOT DONE YET
- `npx astro add tailwind`
- change/create files according to [patchfile]:
  - global.css:
    - add ``@import "tailwindcss";``
  - layouts/Layout.astro
    - (new file for strapi post layout)
  - src/types/strapi.ts
    - (new file contain data linking for promises)
  - src/pages/index.astro
    - (new startpage with strapi posts)
  - .env
    - `STRAPI_URL=http://localhost:1337`
    - for more flexibility

---

---

## authors
- [matt] Code
- [sam] Planning & Mentoring

## links and thanks

- [AWS guide+video on S3 w/ CloudFront and (outdated) OAI][guide_cloudfront]

[integrate]: https://strapi.io/integrations "strapi.io/integrations"
[themes]: https://astro.build/themes/1/?search=&price%5B%5D=free "Free Astro Starter Themes"
[astro]: https://astro.build/ "astro static site generator"
[strapi]: https://strapi.io/ "Strapi CMS - SaaS or selfhosted"

[patchfile]: ./doc/integrate_strapi_into_astro.patch "Patchfile"
[frontend]: ./frontend/ "frontend"
[gitignore]: ./frontend/.gitignore "frontend/.gitignore"
[dist]: ./frontend/dist/ "static website generated(built) by astro using `npm run build`"

[repolink]: https://github.com/Codingschule/aws-astro-headless-cms-deployment "Internal link to this repository"
[matt]: https://github.com/yasuoiwakura "Matthias Block" 
[sam]: https://github.com/hackbraten68 "Sam Dillenburg"

[aws_oac]: https://aws.amazon.com/de/blogs/networking-and-content-delivery/amazon-cloudfront-introduces-origin-access-control-oac/ "AWS OAC INtroduction"
[guide_s3_oac]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html "AWS Site about S3 BucketPolicy regarding OAC and restricted access"
[guide_cloudfront]: https://aws.amazon.com/de/cloudfront/getting-started/S3/ "Amazon CloudFront Tutorials: Setting up a CloudFrotn Distribution"
[Template]: https://github.com/aws-cloudformation/aws-cloudformation-templates/blob/main/S3/compliant-static-website.yaml "complete compliant-static-website.yaml"
[calc]: https://calculator.aws/ "AWS cost calculator"

<!-- 
[Template]: https://github.com/aws-cloudformation/aws-cloudformation-templates/blob/main/S3/compliant-static-website.yaml "complete compliant-static-website.yaml" -->
