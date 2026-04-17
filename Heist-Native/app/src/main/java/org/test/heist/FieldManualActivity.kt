package org.test.heist

import android.os.Bundle
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import android.widget.Button

class FieldManualActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Immersive fullscreen
        window.setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        )
        supportActionBar?.hide()
        setContentView(R.layout.activity_field_manual)

        // Top-left back arrow
        findViewById<androidx.appcompat.widget.AppCompatImageButton>(R.id.backArrowTop)
            .setOnClickListener { finish() }

        // Bottom "Return to Base" button
        findViewById<Button>(R.id.backBtn).setOnClickListener { finish() }
    }

    override fun onBackPressed() {
        super.onBackPressed()
        finish()
    }
}
