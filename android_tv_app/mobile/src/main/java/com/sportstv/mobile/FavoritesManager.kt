package com.sportstv.mobile

import android.content.Context
import android.content.SharedPreferences

object FavoritesManager {
    private const val PREFS_NAME = "sports_tv_mobile_prefs"
    private const val KEY_FAVORITES = "favorite_stream_ids"

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    fun getFavoriteIds(context: Context): Set<Int> {
        val stringSet = getPrefs(context).getStringSet(KEY_FAVORITES, emptySet()) ?: emptySet()
        return stringSet.mapNotNull { it.toIntOrNull() }.toSet()
    }

    fun isFavorite(context: Context, streamId: Int): Boolean {
        return getFavoriteIds(context).contains(streamId)
    }

    fun toggleFavorite(context: Context, streamId: Int): Boolean {
        val current = getFavoriteIds(context).toMutableSet()
        val isFav = if (current.contains(streamId)) {
            current.remove(streamId)
            false
        } else {
            current.add(streamId)
            true
        }
        
        getPrefs(context).edit()
            .putStringSet(KEY_FAVORITES, current.map { it.toString() }.toSet())
            .apply()
            
        return isFav
    }
}
