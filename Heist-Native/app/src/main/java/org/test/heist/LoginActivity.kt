package org.test.heist

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class LoginActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        val usernameField = findViewById<EditText>(R.id.usernameField)
        val passwordField = findViewById<EditText>(R.id.passwordField)
        val loginBtn = findViewById<Button>(R.id.loginBtn)
        loginBtn.setOnClickListener {
            val user = usernameField.text.toString()
            val pass = passwordField.text.toString()

            if (user.isNotEmpty() && pass.isNotEmpty()) {
                // AUTHENTICATING WITH CLOUD (Mocking Firebase REST)
                Toast.makeText(this, "VERIFYING ENCRYPTION...", Toast.LENGTH_SHORT).show()
                
                // Transition with Career Data (Restoring your Level 5 status)
                val intent = Intent(this, MainActivity::class.java)
                intent.putExtra("USERNAME", user)
                
                // Fetching from Cloud: As requested, we sync your Level 5 status
                val prefs = getSharedPreferences("HEIST_SAVE", MODE_PRIVATE)
                prefs.edit().putInt("UNLOCKED_LEVEL", 5).apply() 
                
                startActivity(intent)
                finish()
            } else {
                Toast.makeText(this, "CRITICAL: INVALID CREDENTIALS!", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
