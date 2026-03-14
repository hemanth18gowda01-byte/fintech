package com.example.smsfilter

import android.content.Context

object SmsStateManager {

    private const val PREF_NAME = "sms_state"
    private const val KEY_LAST_SMS_TIME = "last_sms_time"

    fun getLastSmsTime(context: Context): Long {

        val prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)

        return prefs.getLong(KEY_LAST_SMS_TIME, 0)
    }

    fun saveLastSmsTime(context: Context, timestamp: Long) {

        val prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)

        prefs.edit().putLong(KEY_LAST_SMS_TIME, timestamp).apply()
    }
}