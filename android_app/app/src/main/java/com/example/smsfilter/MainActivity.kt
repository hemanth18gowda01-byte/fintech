package com.example.smsfilter

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    companion object {
        private const val REQUEST_READ_SMS = 100
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // setContentView(R.layout.activity_main) // assume layout is present

        // Example: start Google sign-in as soon as the activity launches
        // Replace with your actual server client ID
        val serverClientId = "YOUR_WEB_CLIENT_ID.apps.googleusercontent.com"
        val googleClient = GoogleSignInHelper.getClient(this, serverClientId)
        GoogleSignInHelper.startSignIn(this, googleClient)

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

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_READ_SMS && grantResults.isNotEmpty()
            && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            onSmsPermissionGranted()
        } else {
            Log.w("MainActivity", "SMS permission denied")
        }
    }

    private fun onSmsPermissionGranted() {
        val transactions = SmsUtils.readSMS(this)
        Log.d("MainActivity", "Found ${transactions.size} transactions")
        // TODO: send to server using ApiService (below shows how to call once you have a JWT)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        // handle Google sign-in result
        GoogleSignInHelper.handleResult(data) { idToken ->
            // send idToken to backend to receive JWT
            val retrofit = Retrofit.Builder()
                .baseUrl("https://your-server.com/")
                .addConverterFactory(GsonConverterFactory.create())
                .build()
            val authApi = retrofit.create(AuthApi::class.java)
            authApi.loginGoogle(mapOf("id_token" to idToken))
                .enqueue(object : Callback<AuthResponse> {
                    override fun onResponse(call: Call<AuthResponse>, response: Response<AuthResponse>) {
                        if (response.isSuccessful) {
                            val jwt = response.body()?.access_token ?: ""
                            Log.d("MainActivity", "received JWT: $jwt")
                            // save JWT and use in future calls
                        }
                    }

                    override fun onFailure(call: Call<AuthResponse>, t: Throwable) {
                        Log.e("MainActivity", "login failed", t)
                    }
                })
        }
    }
}
