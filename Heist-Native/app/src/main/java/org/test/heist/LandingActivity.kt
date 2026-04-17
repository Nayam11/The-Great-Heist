package org.test.heist

import android.content.Intent
import android.os.Bundle
import android.view.animation.AnimationUtils
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class LandingActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_landing)

        val title = findViewById<TextView>(R.id.landingTitle)
        val tapText = findViewById<TextView>(R.id.tapToStart)

        // Title Animation (Scaling Pulse)
        val pulse = AnimationUtils.loadAnimation(this, R.anim.pulse_anim)
        title.startAnimation(pulse)

        // Blink Animation for "Tap" text
        val blink = AnimationUtils.loadAnimation(this, R.anim.blink_anim)
        tapText.startAnimation(blink)

        findViewById<android.view.View>(android.R.id.content).setOnClickListener {
            startActivity(Intent(this, LoginActivity::class.java))
            finish()
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
        }
    }
}
