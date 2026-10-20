# Deploying to Cloudflare Pages

This repo can publish its static site to **Cloudflare Pages** as an alternative
to GitHub Pages. GitHub Pages is only available for *private* repositories on
the paid GitHub Pro/Team/Enterprise plans; on the free plan, Pages requires a
**public** repository. Because the contents of this repository are personal
financial data, it should stay private. Cloudflare Pages' free tier supports
**private** GitHub repositories (and allows 500 builds per month), so it is the
free way to publish while keeping the repo private.

## One-time setup

Do these steps once, in order:

1. **Create a Cloudflare account** at <https://dash.cloudflare.com/sign-up>
   (the free plan is enough).

2. **Create a Pages project named `flank-ledger`.**
   In the Cloudflare dashboard, go to *Workers & Pages* → *Create* → *Pages*,
   and name the project `flank-ledger`. (The deploy command in
   `.github/workflows/cloudflare.yml` and `scripts/deploy-cloudflare.sh`
   passes `--project-name=flank-ledger`, so the names must match.)

3. **Create an API token** with the *Cloudflare Pages — Edit* permission:
   go to *My Profile* → *API Tokens* → *Create Token* → *Custom token*, and
   give it the **Cloudflare Pages — Edit** permission. Copy the token; it is
   shown only once.

4. **Find your Account ID.** It is shown in the Cloudflare dashboard on the
   *Workers & Pages* overview page (and in the URL of most dashboard pages).

5. **Add both values as repository secrets.** In the GitHub repository, go to
   *Settings* → *Secrets and variables* → *Actions* → *New repository secret*,
   and add:
   - `CLOUDFLARE_API_TOKEN` — the API token from step 3
   - `CLOUDFLARE_ACCOUNT_ID` — the Account ID from step 4

6. **Push to `main`.** The workflow deploys automatically on every push to
   `main` (and can be triggered manually from the *Actions* tab via
   *workflow_dispatch*).

## A note on visibility

A Cloudflare Pages site is reachable by **anyone who has the URL** — it is not
protected by the repository's private status. Treat the site URL itself as
private: do not share it publicly, and do not link to it from public places.

## Verifying a deploy

1. Open the **Actions** tab in the GitHub repository.
2. Confirm the **"Deploy to Cloudflare Pages"** job went green.
3. Open the URL from the job summary (the *Summary* step prints the deployment
   URL) to check the published site.

## Deploying from your own machine

If you have the Cloudflare CLI installed, you can deploy locally instead of
pushing:

```sh
scripts/deploy-cloudflare.sh
```

The script builds the site first, then runs
`wrangler pages deploy site --project-name=flank-ledger`. If `wrangler` is not
installed, the script prints how to install it (`npm install -g wrangler`).
