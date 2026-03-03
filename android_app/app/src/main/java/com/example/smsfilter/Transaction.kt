package com.example.smsfilter

data class Transaction(
    val amount: Double,          // allow decimals
    val merchant: String,
    val type: String,            // "debit" or "credit"
    val date: String,            // ISO yyyy-MM-dd
    val account: String? = null  // optional account number or mask
)