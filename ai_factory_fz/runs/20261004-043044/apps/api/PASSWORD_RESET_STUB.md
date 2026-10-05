# Password reset stub (Release 2 demo)

Production email is **not** wired for M3 Release 2. When a registered customer calls `POST /api/v1/auth/forgot-password`, the API:

1. Always responds with **202** and the same generic message (no email enumeration).
2. For known, active accounts, creates a hashed `PasswordResetToken` row and invokes `PasswordResetStubService`, which **logs** the plain token and a deep link to the API server console.

## Demo steps

1. Start the API with a reachable database (`npm run start:dev`).
2. Request a reset for a seeded user, e.g. `shopper@example.com` (see catalog/auth seeds if applicable).
3. Watch the server logs for lines prefixed with `[PasswordResetStub]`. The **warn** line contains the plain `token` value.
4. Call `POST /api/v1/auth/reset-password` with JSON:

   ```json
   {
     "token": "<token from log>",
     "newPassword": "NewStr0ngPass!"
   }
   ```

5. Expect **200** and message `Your password has been updated.` Log in with the new password.

The Flutter app uses deep link shape `lumen://auth/reset-password?token=...` (SCR-09); the mobile client reads the query parameter and submits `resetPassword`.

Tokens are single-use, stored as SHA-256 hashes (peppered with `JWT_REFRESH_SECRET`), and expire after `PASSWORD_RESET_EXPIRES_SECONDS` (default **3600** seconds).
