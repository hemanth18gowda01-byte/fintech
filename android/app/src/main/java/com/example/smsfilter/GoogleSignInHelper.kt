package com.example.smsfilter

import android.app.Activity
import android.content.Intent
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInAccount
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.tasks.Task

object GoogleSignInHelper {
    private const val RC_SIGN_IN = 9001

    /**
     * Configure a GoogleSignInClient with requestIdToken.
     * `serverClientId` must be the web application client ID from
     * the Google Cloud Console (OAuth 2.0 credentials).
     */
    fun getClient(activity: Activity, serverClientId: String): GoogleSignInClient {
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(serverClientId)
            .requestEmail()
            .build()
        return GoogleSignIn.getClient(activity, gso)
    }

    fun startSignIn(activity: Activity, client: GoogleSignInClient) {
        val signInIntent: Intent = client.signInIntent
        activity.startActivityForResult(signInIntent, RC_SIGN_IN)
    }

    fun handleResult(data: Intent?, onTokenReceived: (String) -> Unit) {
        val task: Task<GoogleSignInAccount> = GoogleSignIn.getSignedInAccountFromIntent(data)
        try {
            val account = task.getResult(Exception::class.java)
            account?.idToken?.let { token ->
                onTokenReceived(token)
            }
        } catch (e: Exception) {
            // handle sign-in failure
        }
    }
}
