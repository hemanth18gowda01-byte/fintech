package com.example.smsfilter

import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApi {
    @POST("login-google")
    fun loginGoogle(@Body body: Map<String, String>): Call<AuthResponse>
}
