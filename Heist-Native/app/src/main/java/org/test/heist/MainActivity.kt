package org.test.heist

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.setFlags(
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN,
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN
        )
        supportActionBar?.hide()
        setContentView(R.layout.activity_main)

        val username = intent.getStringExtra("USERNAME") ?: "GUEST"
        findViewById<TextView>(R.id.usernameLabel).text = "OPERATIVE: ${username.uppercase()}"

        // Start Mission → Level Select
        findViewById<Button>(R.id.startBtn).setOnClickListener {
            startActivity(Intent(this, LevelSelectActivity::class.java))
        }

        // Field Manual / Game Guide
        findViewById<Button>(R.id.guideBtn).setOnClickListener {
            startActivity(Intent(this, FieldManualActivity::class.java))
        }

        // Support page
        findViewById<Button>(R.id.supportBtn).setOnClickListener {
            startActivity(Intent(this, SupportActivity::class.java))
        }

        // Quit — confirm then close app
        findViewById<Button>(R.id.quitBtn).setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("QUIT")
                .setMessage("Abort mission and exit the app?")
                .setPositiveButton("QUIT") { _, _ ->
                    finishAffinity()           // closes all activities
                }
                .setNegativeButton("CANCEL", null)
                .show()
        }
    }

    // Disable physical back on menu (must use Quit button)
    override fun onBackPressed() {
        // intentionally suppressed — use Quit button
    }
}