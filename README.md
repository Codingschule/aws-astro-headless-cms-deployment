# aws-astro-headless-cms-deployment
deployment part of website
This readme will mainly serve as documentation and optionally as guided landing page for this project.

You can clone this repo for a template of deploying a SSG website on AWS.
Or you can use it as walkthrough to build your own.

## directory structure

- frontend ontains the astro static site generator (ssg) project
- cloudformation for provisioning AWS infrastructure
- doc example files

## scafffold Astro (if not cloning this repo)

- install NodeJs for your OS
- clone or create new git repo
- choose a [theme][themes] (we go with "blog" and have a [patchfile][patchfile] for optionalle integrating strapi)
- cd into repo dir
- `npm create astro@latest -- --template blog frontend`
  - will generate an [astro] project
  - in case npm depency installation fails, close your loud sync, give your virus scanner 1-2 minutes (it probably checks npm_nodes) and run:
    - cd frontend
    - npm install

### build astro and run webserver

You can now build html files from your astro project
- cd frontend
- spin up a **dev**eloper webserver whilst working on your files:
  - `npm run dev` this will...
  - spin up webserver on http://localhost:4321/
  - ~~will open browser~~
- build your static website
  - `npm run build`
  - will store into "dist", which is ignored through [gitignore]

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

## authors

## links


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

[calc]: https://calculator.aws/ "AWS cost calculator"

<!-- 
[Template]: https://github.com/aws-cloudformation/aws-cloudformation-templates/blob/main/S3/compliant-static-website.yaml "complete compliant-static-website.yaml" -->
