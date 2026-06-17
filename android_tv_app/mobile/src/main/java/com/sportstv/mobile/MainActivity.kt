package com.sportstv.mobile

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.sportstv.mobile.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Add a default placeholder text in FrameLayout
        val textView = TextView(this).apply {
            text = "Welcome to Sports TV Mobile!"
            textSize = 20f
            gravity = android.view.Gravity.CENTER
        }
        binding.container.addView(textView)

        binding.navView.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    textView.text = "Home screen placeholder"
                    true
                }
                R.id.navigation_favorites -> {
                    textView.text = "Favorites screen placeholder"
                    true
                }
                else -> false
            }
        }
    }
}
