package org.test.heist

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.GridLayout
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.setPadding

class LevelSelectActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.setFlags(
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN,
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN
        )
        supportActionBar?.hide()
        setContentView(R.layout.activity_level_select)

        // Back arrow → return to menu
        findViewById<androidx.appcompat.widget.AppCompatImageButton>(R.id.backArrow)
            .setOnClickListener { finish() }

        val prefs = getSharedPreferences("HEIST_SAVE", MODE_PRIVATE)
        val unlockedLevel = prefs.getInt("UNLOCKED_LEVEL", 1)
        val grid = findViewById<GridLayout>(R.id.levelGrid)

        for (i in 1..20) {
            val btn = Button(this)
            btn.text = "$i"

            val isUnlocked = i <= unlockedLevel
            btn.setBackgroundColor(
                android.graphics.Color.parseColor(if (isUnlocked) "#FFD700" else "#222233")
            )
            btn.setTextColor(
                if (isUnlocked) android.graphics.Color.BLACK else android.graphics.Color.parseColor("#555566")
            )
            btn.isEnabled = isUnlocked

            val params = GridLayout.LayoutParams()
            params.width = 150
            params.height = 150
            params.setMargins(15, 15, 15, 15)
            btn.layoutParams = params

            btn.setOnClickListener {
                val intent = Intent(this, GameActivity::class.java)
                intent.putExtra("LEVEL", i)
                startActivity(intent)
            }
            grid.addView(btn)
        }
    }

    override fun onBackPressed() {
        super.onBackPressed()
        finish()
    }
}
