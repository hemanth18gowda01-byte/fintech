# Android SMS Filter App

This module contains a minimal Android project with the logic for
reading bank-related SMS messages, filtering them in three layers, and
sending the extracted transactions to a remote server JSON via Retrofit.

The important pieces are located under `app/src/main/java/com/example/smsfilter`:

* `MainActivity.kt` – asks for SMS permission and kicks off the reader.
* `SmsUtils.kt` – contains the `readSMS`, filter and extraction helpers.
* `Transaction.kt` – data class representing a parsed transaction (amount, merchant, type, date and optional account number).
* `ApiService.kt` – Retrofit interface for the `/sync-transactions` endpoint.
* `GoogleSignInHelper.kt` – helper for obtaining a Google ID token used by the backend for authentication.
* `AuthApi.kt`/`AuthResponse.kt` – Retrofit interfaces to exchange the Google ID token for a JWT and hold the response.


## Google authentication

To authenticate users with Google Sign-In:

1. Create OAuth2 credentials (web application) in the Google Cloud Console and copy the **client ID**.
2. Call `GoogleSignInHelper.getClient(this, serverClientId)` from an activity and start the sign-in flow.
3. In `onActivityResult` call `GoogleSignInHelper.handleResult(...)` to receive the ID token.
4. POST the token to `/login-google` on the Flask backend; you will receive a JWT access token in the response.
5. Use that JWT when calling `/sync-transactions` by setting the `Authorization: Bearer <token>` header.

You can open this directory in Android Studio and convert it into a
full Gradle project; the files here demonstrate the core logic only.