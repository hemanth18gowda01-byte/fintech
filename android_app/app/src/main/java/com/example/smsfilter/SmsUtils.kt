package com.example.smsfilter

import android.content.Context
import android.net.Uri
import java.text.SimpleDateFormat
import java.util.*

object SmsUtils {

    /**
     * Read all SMS in the inbox and return parsed bank transactions.
     * Caller must have runtime permission granted beforehand.
     */
    fun readSMS(context: Context): List<Transaction> {
        val transactions = mutableListOf<Transaction>()
        val uri = Uri.parse("content://sms/inbox")

        context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            while (cursor.moveToNext()) {
                val sender = cursor.getString(cursor.getColumnIndexOrThrow("address")) ?: ""
                val body = cursor.getString(cursor.getColumnIndexOrThrow("body")) ?: ""
                val dateMillis = cursor.getLong(cursor.getColumnIndexOrThrow("date"))

                if (isBankSender(sender) && isTransactionMessage(body)) {
                    extractTransaction(body, dateMillis)?.let { transactions.add(it) }
                }
            }
        }

        return transactions
    }

    // Layer 1: look for a known bank keyword in the sender address
    fun isBankSender(sender: String): Boolean {
        val banks = listOf("HDFC", "SBI", "ICICI", "AXIS")
        return banks.any { sender.contains(it, ignoreCase = true) }
    }

    // Layer 2: include/exclude keywords to discard OTPs, adverts, etc.
    fun isTransactionMessage(body: String): Boolean {
        val includeWords = listOf("debited", "credited", "UPI", "Rs", "INR")
        val excludeWords = listOf("OTP", "verification", "password")
        val containsInclude = includeWords.any { body.contains(it, true) }
        val containsExclude = excludeWords.any { body.contains(it, true) }
        return containsInclude && !containsExclude
    }

    // Layer 3: extract amount, type, merchant and format date
    fun extractTransaction(body: String, dateMillis: Long): Transaction? {
        // amounts may have commas/decimals
        val amountRegex = Regex("Rs\\.?\\s?([0-9,]+(?:\\.[0-9]{1,2})?)")
        val typeRegex = Regex("(debited|credited)", RegexOption.IGNORE_CASE)
        // merchant may include spaces, digits & ampersand
        val merchantRegex = Regex("at\\s+([A-Za-z0-9 &]+)", RegexOption.IGNORE_CASE)
        // account numbers often appear as A/c XXXX1234 or Acct. XXXXX
        val accountRegex = Regex("A/c\\s*([A-Za-z0-9#*xX]+)", RegexOption.IGNORE_CASE)

        val amtMatch = amountRegex.find(body)
        val typeMatch = typeRegex.find(body)
        val merchMatch = merchantRegex.find(body)
        val acctMatch = accountRegex.find(body)

        if (amtMatch != null && typeMatch != null && merchMatch != null) {
            val rawAmt = amtMatch.groupValues[1].replace(",", "")
            val amount = rawAmt.toDoubleOrNull() ?: return null
            val type = typeMatch.value.lowercase(Locale.getDefault())
            val merchant = merchMatch.groupValues[1].trim()
            val account = acctMatch?.groupValues?.get(1)
            val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val date = sdf.format(Date(dateMillis))
            return Transaction(amount, merchant, type, date, account)
        }
        return null
    }
}
