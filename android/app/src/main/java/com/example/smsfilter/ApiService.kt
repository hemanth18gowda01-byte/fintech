package com.example.smsfilter

import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST

interface ApiService {
    @POST("sync-transactions")
    fun syncTransactions(
        @Header("Authorization") token: String,
        @Body transactions: List<Transaction>
    ): Call<ResponseBody>
}
