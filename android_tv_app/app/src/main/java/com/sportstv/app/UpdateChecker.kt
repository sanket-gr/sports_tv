package com.sportstv.app

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.util.Log
import android.app.AlertDialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

object UpdateChecker {
    private const val TAG = "UpdateChecker"

    suspend fun checkForUpdate(activity: Activity, showToastIfLatest: Boolean = false) {
        val versionInfo = withContext(Dispatchers.IO) {
            try {
                ApiClient.service.getVersion()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to check for updates", e)
                null
            }
        } ?: run {
            if (showToastIfLatest) {
                withContext(Dispatchers.Main) {
                    android.widget.Toast.makeText(activity, "Failed to connect to update server.", android.widget.Toast.LENGTH_SHORT).show()
                }
            }
            return
        }

        val currentVersionCode = BuildConfig.VERSION_CODE
        Log.d(TAG, "Current version: $currentVersionCode, server version: ${versionInfo.versionCode}")

        if (versionInfo.versionCode <= currentVersionCode) {
            if (showToastIfLatest) {
                withContext(Dispatchers.Main) {
                    android.widget.Toast.makeText(activity, "App is already up to date (v${versionInfo.versionName})", android.widget.Toast.LENGTH_SHORT).show()
                }
            }
            return
        }

        withContext(Dispatchers.Main) {
            showUpdateDialog(activity, versionInfo)
        }
    }

    private fun showUpdateDialog(activity: Activity, versionInfo: com.sportstv.app.model.VersionInfo) {
        if (activity.isFinishing || activity.isDestroyed) return

        AlertDialog.Builder(activity)
            .setTitle("Update Available (v${versionInfo.versionName})")
            .setMessage(versionInfo.releaseNotes)
            .setCancelable(false)
            .setPositiveButton("Update Now") { dialog, _ ->
                dialog.dismiss()
                try {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(versionInfo.apkUrl))
                    activity.startActivity(intent)
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to open update URL", e)
                }
            }
            .setNegativeButton("Later") { dialog, _ ->
                dialog.dismiss()
            }
            .show()
    }
}
