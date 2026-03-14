package com.example.smsfilter

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class MainActivity : AppCompatActivity() {
    companion object {
        private const val REQUEST_READ_SMS = 100
        private const val RC_SIGN_IN       = 9001
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // setContentView(R.layout.activity_main)

        // ── Step 1: Start Google Sign-In ──────────────────────────────────
        // REPLACE this string with your real Web Client ID from Google Cloud Console
        val serverClientId = "YOUR_WEB_CLIENT_ID.apps.googleusercontent.com"
        val googleClient   = GoogleSignInHelper.getClient(this, serverClientId)
        GoogleSignInHelper.startSignIn(this, googleClient)

        // ── Step 2: Request SMS permission ───────────────────────────────
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.READ_SMS),
                REQUEST_READ_SMS
            )
        } else {
            onSmsPermissionGranted()
        }
    }

    // ── Called when user taps Allow on SMS dialog ─────────────────────────
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_READ_SMS
            && grantResults.isNotEmpty()
            && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            onSmsPermissionGranted()
        } else {
            Log.w("MainActivity", "SMS permission denied")
        }
    }

    // ── Read SMS → send to backend ────────────────────────────────────────
    private fun onSmsPermissionGranted() {
        val transactions = SmsUtils.readSMS(this)
        Log.d("MainActivity", "Found ${transactions.size} transactions")

        val jwt = getSharedPreferences("fintrack", MODE_PRIVATE)
            .getString("jwt", null) ?: run {
                Log.w("MainActivity", "No JWT — waiting for Google login to complete")
                return
            }

        val retrofit = Retrofit.Builder()
            .baseUrl("https://fintech-2-0.onrender.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        retrofit.create(ApiService::class.java)
            .syncTransactions("Bearer $jwt", transactions)
            .enqueue(object : Callback<ResponseBody> {
                override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                    Log.d("MainActivity", "Sync success — HTTP ${response.code()}")
                }
                override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                    Log.e("MainActivity", "Sync failed: ${t.message}")
                }
            })
    }

    // ── Google Sign-In result ─────────────────────────────────────────────
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode != RC_SIGN_IN) return  // ignore unrelated results

        GoogleSignInHelper.handleResult(data) { idToken ->
            val retrofit = Retrofit.Builder()
                .baseUrl("https://fintech-2-0.onrender.com/")
                .addConverterFactory(GsonConverterFactory.create())
                .build()

            retrofit.create(AuthApi::class.java)
                .loginGoogle(
                        mapOf(
                            "google_id" to idToken
                        )
                )
                .enqueue(object : Callback<AuthResponse> {
                    override fun onResponse(call: Call<AuthResponse>, response: Response<AuthResponse>) {
                        if (response.isSuccessful) {
                            val jwt = response.body()?.access_token ?: return
                            Log.d("MainActivity", "JWT received")

                            // Save JWT for future use
                            getSharedPreferences("fintrack", MODE_PRIVATE)
                                .edit()
                                .putString("jwt", jwt)
                                .apply()

                            // Now read and sync SMS
                            onSmsPermissionGranted()
                        }
                    }
                    override fun onFailure(call: Call<AuthResponse>, t: Throwable) {
                        Log.e("MainActivity", "Login failed: ${t.message}")
                    }
                })
        }
    }
}
