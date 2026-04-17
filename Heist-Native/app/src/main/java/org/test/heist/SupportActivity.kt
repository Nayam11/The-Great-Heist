package org.test.heist

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class SupportActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.setFlags(
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN,
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN
        )
        supportActionBar?.hide()
        setContentView(R.layout.activity_support)

        // Back arrow returns to menu
        findViewById<androidx.appcompat.widget.AppCompatImageButton>(R.id.backArrow)
            .setOnClickListener { finish() }
    }

    // Physical back button also works
    override fun onBackPressed() {
        super.onBackPressed()
        finish()
    }
}
