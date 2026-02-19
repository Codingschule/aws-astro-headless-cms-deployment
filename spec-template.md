# Spec-Driven Development Template

Dieses Dokument enthält grundlegende Gedanken zum Projekt und ist hauptsächlich als Leitplanke für den Coding-Agent gedacht.
`/README.md` enthält die Dokumentation für den User der dieses Projekt praktisch nachvollziehen und anwenden möchte. Bei Projektfortschritt sollte sie aktuelisiert werden. Falls alte Lösungansätze im Projektfortschritt ersetzt werden, soll die alte Lösung als seperate .md Datei in /doc dokumentiert und in der README verlinkt werden.

---
## 1. Projektübersicht

| Element | Beschreibung |
|---------|--------------|
| **Projektname** | `aws-sam-astro-poc` |
| **Ziel** | Lernprojekt für AWS SAM / CloudFormation, Astro SSG + Serverless Functions & AWS Actions Build Pipeline |
| **Technologien** | AWS SAM, CloudFormation, Astro, Node.js, GitHub Actions, Lambda, DynamoDB, IP-Gateway, CloudFront CDN, S3 |

## 2. Annahmen

1. **AWS Account**: Ein AWS-Konto mit Zugriff auf SAM, Lambda und CloudFront ist vorhanden.
2. **IAM Berechtigungen**: Der Entwickler hat die notwendigen IAM-Berechtigungen für SAM Deployments (`sam deploy`) und S3 Bucket Management.
3. **Build-Server**: GitHub Actions wird als CI/CD verwendet. Die Authentifizierung erfolgt über STS über AWS OIDC-Provider. Die folgenden Repository Variables sind erforderlich:
   - `AWS_ROLE_ARN`
   - `AWS_REGION`
   - (bitte anhand der pipeline und SAM template ergänzen)
4. **Domain & Zertifikat**: Default ist die automatisch zugewiuesene CloudFront Domain. Optional soll eine Custom Domain ermöglicht werden.
5. **Code-Repository**: Der Quellcode befindet sich in einem GitHub‑Repo:
   - `/template.yml` das SAM template, sowie `/cloudformation` alte oder spin-off Versionen des Provisioning
     - `/ephemeral_oidc_bootstrap` enthält den optionalen Nested SAM-Stack `./template.yml` für den OIDC-Provider als CustomResource nebst Lambda Funktion `./py_create_oidc/`.
     - `/samconfig.toml` enthält die Deployment-Parameter für SAM
   - `/.github/workflows/deploy.yml` Deploy Pipeline zum bauen und updaten von Astro. Wird archiviert (Kopie) und dann erweitert um aws SAM build/deploy zu unterstützen.
   - `/doc` enthält Codeschnipsel und detailierte Erklärungen zu einzelnen Aspekten oder verworfenen Umsetzungen
   - `frontend/` hat die Astro Webseite:
     - frontend/src der Astro Quelltext
     - frontend/dict das Astro Artefakt
   - `backend/guestbook` die Serverless Funktionen als NodeJS
     -  und `infra/` nutzt.
6. **Node.js Version**: Node 24.x (Fakten: Node 20.x ist/bald EOL! Node 24.x ist bei AWS verfügbar!)
7. **Datenpersistenz**: Der statische Teil der Webseite wird im repo gespeichert, dynamische Komponenten serverless in einfachen DynamoDB Tables. Später wird ein Headless CMS als dritte Datenquelle integriert.
8. **Monitoring**: CloudWatch Logs sind für Lambda‑Funktionen aktiviert, es ist wichtig dass der Entwickler zum Lernen alle Debuggingoptionen hat.

## 3. Funktionale Anforderungen

(diese Beispielvorgaben sind unpeprüft und entsprechen ggf. nicht den realen Vorgaben und müssen ggf. an das Projekt angepasst werden)

| ID | Feature | Akzeptanzkriterien |
|----|---------|---------------------|
| FR-01 | Astro build | Der Befehl `npm run build` erzeugt einen `dist/` Ordner mit statischen HTML/CSS/JS.
| FR-02 | Serverless API | Lambda‑Funktion `/api/*` liefert JSON‑Antworten, z.B. `/api/time` → `{ "time": "2026-02-18T..." }`.
| FR-03 | CI/CD Pipeline | `sam deploy --stack-name <name>` wird automatisch bei jedem Push in `main` ausgeführt.
| FR-04 | S3 Deployment | Buildartefakte werden in einen S3‑Bucket (`astro-poc-bucket`) hochgeladen und CloudFront invalidiert.

## 4. Nicht-funktionale Anforderungen

* **Performance**: Lambda-Funktionen haben ein Timeout von 15s.
* **Sicherheit**: Alle API-Endpunkte sind authentifiziert via Cognito (optional).
* **Skalierbarkeit**: CloudFront nutzt Edge‑Locations, S3 Bucket ist global.

## 5. Testfälle

Aktuell wird nur der build auf GitHub Actions gebaut und bei Erfolg gepusht.
Der Projektowner/Lernende ist aktuell nicht mit Node JS Entwicklung und Unit tests vertraut, insbesondere nicht in einer GitHub Actions Pipeline für AWS/SAM. Daher sind die Angaben unvollständig, da diese erst in Erfahrung gebracht werden müssen, sobald die eigentliche Funktion des Serverless Guestbook vorhanden ist.

### später erst:
1. **Unit-Test**: `npm test` führt Jest-Tests für Lambda-Funktionen aus.
2. **Integrationstest**: Postman Collection prüft `/api/time` und `/api/hello`.
3. **E2E**: Cypress testet die generierte Seite auf `/index.html`.

## 6. Deployment‑Plan

### Old build (while developing guestbook):
0. Provisioning and initial deployment by user
1. Push or PR auf dev → GitHub Actions → build Astro dist from src
2. (only Push): Upload dist to S3
3. (only Push): Invalidate Cache

### New build (after guestbook is developed): 
1. Push or PR to dev → GitHub Actions
   1.  build Astro dist from src
   2.  (test backend functions?)
   3.  check SAM linting (if possible, test deployment without actually deploying)
2. Only on push:
   1. Deploy/update SAM Stack
   2. Invalidate CDN cache
   3. Invalidate Cache

## Tickets für implementierung von Serverless Funktionen (Reihenfolge ggf. flexibel):

siehe `/TODO.md`

## changelog and versionierung

Changelog - bitte anhand der Merges erstellen. Als Versionierung die dreistellige Zahl aus den feature-branches (.git commits und merges nach dev branch) verwenden.

---

