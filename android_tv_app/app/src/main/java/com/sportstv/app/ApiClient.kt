package com.sportstv.app

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

// ─── Backend URL configuration ───────────────────────────────────────────────
// IMPORTANT: Change this to your PC's local IP when testing on a real TV device.
// Use "http://10.0.2.2:8000/" ONLY for Android Studio emulator.
// Use "http://192.168.100.58:8000/" for a real TV on the same WiFi network.
//
// TIP: Run `ipconfig` on your PC and use the IPv4 address shown.
const val BASE_URL = "http://192.168.100.58:8000/"

// ─── Retrofit interface ──────────────────────────────────────────────────────
interface SportsApiService {

    @GET("api/streams")
    suspend fun getStreams(
        @Query("live_only") liveOnly: Boolean = true,
    ): List<StreamItem>

    @GET("api/streams/{id}")
    suspend fun getStream(
        @Path("id") id: Int,
    ): StreamItem

    /** Triggers re-extraction on backend; returns current data (may still be old URL).
     *  Poll getStream() after ~10s to get the fresh HLS URL. */
    @GET("api/streams/{id}/refresh")
    suspend fun refreshStream(
        @Path("id") id: Int,
    ): StreamItem

    @GET("api/categories")
    suspend fun getCategories(): List<CategoryItem>
}

// ─── Singleton client ─────────────────────────────────────────────────────────
object ApiClient {
    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BASIC
    }

    private val httpClient = OkHttpClient.Builder()
        .addInterceptor(logging)
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    val service: SportsApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SportsApiService::class.java)
    }
}
