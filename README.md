# banking-app (EastWest Bank)

Flask banking app for the QR payment prototype. Handles account
selection, payment confirmation, debit/credit settlement, and QR
generation for the ecommerce app to embed.

## What changed from the frontend-preview version

The UI and models were already solid. What was missing:

- Database wiring was fully commented out (`app.py` never called
  `db.init_app()`); `utils/helpers.py` returned hardcoded mock accounts.
  Both are now real, using exactly the SQLAlchemy logic that was already
  sketched in the original TODO comments.
- There was no `POST /api/payment-requests` endpoint and no webhook call
  back to the ecommerce app after settlement - both added.
- The old `/pay?order_id=...&amount=...&merchant=...` flow trusted the
  URL/form for the amount and merchant - a real tampering risk, since
  anyone could edit those before opening the link. Replaced with
  `/pay/<transaction_id>`, which looks amount/merchant up from a new
  `PaymentRequest` DB row created by the API call. Nothing the browser
  sends can change how much money moves.
- Login is now required before paying, and there's no account picker -
  a user logs into their own account, and that's the account that pays.
  `account_id` comes only from the session from here on, never from a
  form field, closing a second tampering path (a user could previously
  edit a hidden `account_id` input to pay from someone else's account).
- The balances dashboard is admin-only. Admin is a separate login
  (`AdminUser`), deliberately not an `Account` - admin can view
  everything but was never given the ability to hold or move money.
- Port changed from 5000 to 5001 (5000 collides with the ecommerce app);
  health check now returns `{"status": "ok"}` to match the rest of the
  project's convention.

## Logging in

Demo credentials (training project only - never reuse this pattern
anywhere real money is involved):

| Username | Password | Role |
|---|---|---|
| `jdoe` | `password123` | Consumer (John Doe) |
| `jsmith` | `password123` | Consumer (Jane Smith) |
| `acruz` | `password123` | Consumer (Alex Cruz) |
| `admin` | `admin123` | Admin - dashboard only, holds no balance |

Opening `/pay/<transaction_id>` while logged out redirects to `/login`
and returns you to that exact payment afterward. The dashboard
(`/`, `/dashboard`) does the same, but only an admin login gets through.

## The contract with the ecommerce app

```
POST /api/payment-requests   (server-to-server, ecommerce -> bank)
Body: {order_id, amount, merchant_account, callback_url, return_url?}
Response: {transaction_id, qr_url}
```

`qr_url` points at `GET /qr/<transaction_id>.png`, generated on demand
(no file storage - works the same with any number of replicas later).
The QR itself encodes a URL to `/pay/<transaction_id>`, not raw payment
details, so scanning it can't be used to forge a different amount.

After the customer selects an account and confirms, this app calls the
`callback_url` it was given:

```
POST <callback_url>
Body: {order_id, status: "PAID" | "FAILED", transaction_id}
```

This call is best-effort - if the ecommerce app is unreachable, the
money has still moved on our side (we don't reverse a real settlement
just because a notification failed). The ecommerce app's order simply
stays `PENDING` until it hears from us, which is the safe failure mode.

## Environment variables

The app uses SQLite automatically when `DB_HOST` is not set. The local
database is created at `instance/banking.db`, and is ignored by Git.
To use MySQL later, set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and
`DB_PASSWORD` in `.env`. `callback_url` and `return_url` arrive
per-request from the ecommerce app's API call, not as environment
config.

## Run locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # leave DB_HOST commented out for SQLite
python app.py           # :5001, auto-seeds demo accounts on first run
```

On Windows PowerShell, activate the environment with
`\.venv\Scripts\Activate.ps1` (or `venv\Scripts\Activate.ps1` if you
used that directory name). Open http://localhost:5001 after the server
starts. To switch to MySQL, uncomment and fill in the `DB_*` values in
`.env`, then restart the app.

Seeding is automatic and idempotent (runs inside `create_app()`) - you
don't need to run `seed.py` by hand, though `python seed.py` still works
standalone if you want to re-seed without starting the server.

## Run with Docker

```bash
docker compose up --build
```

Brings up MySQL and the app together, same pattern as the ecommerce
app's compose file. Note: MySQL's `3306:3306` port mapping here is fine
for standalone local dev, but drop it once this merges into the shared
Dev VM's compose file - port 3306 must never be reachable outside the
VM (SSH tunnel only), per the Dev VM setup guide.

## Manual demo pages (not part of the real integration)

- `/qr` - simulates a merchant checkout by calling the real
  `POST /api/payment-requests` endpoint and showing the QR it gets back.
  Useful for testing this app in isolation, without a running ecommerce
  app.
- `/qr-scanner` - uses your device camera (jsQR) to scan a QR and open
  the resulting `/pay/<transaction_id>` link. Also works by pasting a
  URL manually if you don't have a camera handy.

## What was verified end to end

Ran the real app (not just a syntax check) through the full loop: create
a payment request, log in as a consumer, confirm you land directly on
your own account with no picker, settle, receive the webhook with the
correct payload, and confirm the balance moved by the right amount.
Also verified: an unauthenticated request to `/pay/<id>` or `/dashboard`
correctly redirects to `/login`; a wrong password is rejected; a
consumer login cannot reach the admin dashboard; an admin login cannot
reach the payment flow (no `account_id` in that session at all); and
re-visiting an already-settled transaction 404s.

This used a minimal in-memory stand-in for Flask-SQLAlchemy (real
`flask_sqlalchemy`/`PyMySQL` weren't installable in the sandbox this was
built in) - so real MySQL behavior (constraints, transactions, real
`Numeric` typing) still needs a real run before this ships. Two bugs
were actually found and fixed this way: `PaymentRequest.amount` wasn't
being cast to `Decimal` at creation time, and `Account.balance`
(seeded as plain floats) can't be arithmetic'd against a `Decimal`
without an explicit cast - both fixed at the point of use rather than
relying on implicit DB-refresh type coercion.

## Not done yet / worth doing next

- No automated pytest suite yet (the ecommerce app has one you can use
  as a template - same in-memory-SQLite-per-test pattern would work
  here once real `flask_sqlalchemy` is available to run it against).
- No login/auth gate before account selection - matches the current
  scope, but worth a deliberate decision either way before this is
  called "done."
