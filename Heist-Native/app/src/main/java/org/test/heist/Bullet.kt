package org.test.heist

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Matrix
import android.graphics.Paint
import kotlin.math.*

class Bullet(val context: Context, var x: Float, var y: Float, targetX: Float, targetY: Float, val owner: String, private val bulletBitmap: Bitmap?) {
    var speed = 25f
    var damage = if (owner == "enemy") 10 else 25
    val size = 20f
    
    private var dx: Float = 0f
    private var dy: Float = 0f
    private var angle: Float = 0f
    private var distanceTravelled = 0f
    private val maxRange = 800f
    private val matrix = Matrix()

    init {
        val distX = targetX - x
        val distY = targetY - y
        val dist = sqrt(distX * distX + distY * distY)
        
        if (dist > 0) {
            dx = distX / dist
            dy = distY / dist
        } else {
            dx = 1f; dy = 0f
        }
        
        angle = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble()).toDouble()).toFloat()
    }

    fun update() {
        x += dx * speed
        y += dy * speed
        distanceTravelled += speed
    }

    fun isDead(): Boolean {
        return distanceTravelled >= maxRange
    }

    fun draw(canvas: Canvas, cameraX: Float, cameraY: Float) {
        bulletBitmap?.let { bmp ->
            matrix.reset()
            matrix.postRotate(angle, bmp.width / 2f, bmp.height / 2f)
            matrix.postTranslate(x - cameraX - bmp.width / 2f, y - cameraY - bmp.height / 2f)
            canvas.drawBitmap(bmp, matrix, null)
        }
    }
}
