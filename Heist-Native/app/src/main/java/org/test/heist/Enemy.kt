package org.test.heist

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Matrix
import android.graphics.Paint
import java.util.Random
import kotlin.math.*

class Enemy(val context: Context, var x: Float, var y: Float, private val enemyBitmap: Bitmap?) {
    val size = 80f                      // Slightly smaller hitbox
    var health = 100
    var speed = 3f
    var angle = 0f

    private var state = "patrol"
    private var targetX = x
    private var targetY = y
    private var level = 1
    private val sightRange = 550f
    private val shootRange = 450f       // Only shoot within shorter range to avoid wall shots

    // Stuck detection
    private var stuckTimer = 0
    private var lastX = x
    private var lastY = y

    // Combat
    private var shootTimer = 0
    private var shootDelay = 45

    private val random = Random()
    private val matrix = Matrix()
    private val healthPaint = Paint()

    init {
        targetX = x + random.nextInt(300) - 150
        targetY = y + random.nextInt(300) - 150
    }

    fun setLevel(l: Int) {
        level = l
        speed = 2.5f + (l * 0.15f)
        shootDelay = maxOf(25, 50 - (l * 2))
    }

    fun investigate(ix: Float, iy: Float) {
        if (state != "attack") {
            state = "investigate"
            targetX = ix; targetY = iy
        }
    }

    fun update(playerX: Float, playerY: Float, tileMap: TileMap, bulletBmp: Bitmap?): Bullet? {
        val dx = playerX - x
        val dy = playerY - y
        val distToPlayer = sqrt(dx * dx + dy * dy)

        var spawnedBullet: Bullet? = null

        // ── Sight & Shooting: only fire if there's a clear line-of-sight ──
        val hasLOS = distToPlayer < sightRange && hasLineOfSight(x, y, playerX, playerY, tileMap)

        if (hasLOS) {
            state = "attack"
            targetX = playerX
            targetY = playerY
            angle = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble())).toFloat()

            // Only shoot if ALSO within shoot range (prevents wall-snipe from far away)
            if (distToPlayer < shootRange && shootTimer <= 0) {
                spawnedBullet = Bullet(context, x, y, playerX, playerY, "enemy", bulletBmp)
                shootTimer = shootDelay
            } else if (shootTimer > 0) {
                shootTimer--
            }
        } else {
            if (state == "attack") {
                // Lost sight — move to last known position
                state = "investigate"
            }
            if (shootTimer > 0) shootTimer--
        }

        // ── Movement AI ──
        val tdx = targetX - x
        val tdy = targetY - y
        val distToTarget = sqrt(tdx * tdx + tdy * tdy)

        if (distToTarget > 20f) {
            if (state != "attack") {
                angle = Math.toDegrees(atan2(tdy.toDouble(), tdx.toDouble())).toFloat()
            }

            val nx = x + (tdx / distToTarget) * speed
            val ny = y + (tdy / distToTarget) * speed

            // Multi-point bounding box collision (half-size = 38px)
            val r = size / 2f - 6f
            val moved = when {
                canMoveBox(nx, y, r, tileMap)  -> { x = nx; true }
                canMoveBox(x, ny, r, tileMap)  -> { y = ny; true }
                else -> false
            }

            if (!moved) {
                // Pick a new random target when blocked
                targetX = x + random.nextInt(400) - 200f
                targetY = y + random.nextInt(400) - 200f
                stuckTimer = 0
            }
        } else {
            // Reached target — pick new patrol destination
            if (state == "patrol" || state == "investigate") {
                state = "patrol"
                targetX = x + random.nextInt(400) - 200f
                targetY = y + random.nextInt(400) - 200f
            }
        }

        // ── Stuck detection: if barely moved in 120 frames, get new target ──
        stuckTimer++
        if (stuckTimer >= 120) {
            val movedDist = sqrt((x - lastX).pow(2) + (y - lastY).pow(2))
            if (movedDist < 10f && state != "attack") {
                targetX = x + random.nextInt(500) - 250f
                targetY = y + random.nextInt(500) - 250f
            }
            lastX = x; lastY = y; stuckTimer = 0
        }

        return spawnedBullet
    }

    /**
     * Multi-point AABB collision — checks 4 corners of the enemy's bounding circle.
     * Prevents clipping into walls from any edge.
     */
    private fun canMoveBox(nx: Float, ny: Float, r: Float, tileMap: TileMap): Boolean {
        val ts = tileMap.tileSize
        // Check all 4 corners of the bounding box
        val corners = listOf(
            Pair(nx - r, ny - r), Pair(nx + r, ny - r),
            Pair(nx - r, ny + r), Pair(nx + r, ny + r)
        )
        for ((cx, cy) in corners) {
            val gx = (cx / ts).toInt()
            val gy = (cy / ts).toInt()
            if (gx !in 0 until tileMap.mapWidth || gy !in 0 until tileMap.mapHeight) return false
            val t = tileMap.grid[gy][gx]
            if (t == 1 || t == 4) return false
        }
        return true
    }

    /**
     * DDA ray-cast line-of-sight check.
     * Walks tiles along the line from (x1,y1) to (x2,y2).
     * Returns false if any wall tile (1) is crossed.
     */
    private fun hasLineOfSight(x1: Float, y1: Float, x2: Float, y2: Float, tileMap: TileMap): Boolean {
        val ts = tileMap.tileSize.toFloat()
        val steps = (sqrt((x2 - x1).pow(2) + (y2 - y1).pow(2)) / (ts * 0.5f)).toInt() + 1
        for (i in 0..steps) {
            val t = i.toFloat() / steps
            val sx = x1 + (x2 - x1) * t
            val sy = y1 + (y2 - y1) * t
            val gx = (sx / ts).toInt()
            val gy = (sy / ts).toInt()
            if (gx in 0 until tileMap.mapWidth && gy in 0 until tileMap.mapHeight) {
                if (tileMap.grid[gy][gx] == 1) return false   // Wall blocks LOS
            }
        }
        return true
    }

    fun draw(canvas: Canvas, cameraX: Float, cameraY: Float) {
        val sx = x - cameraX
        val sy = y - cameraY

        if (enemyBitmap != null) {
            matrix.reset()
            // Enemy asset: faces right by default — same convention as player
            matrix.postRotate(angle, enemyBitmap.width / 2f, enemyBitmap.height / 2f)
            matrix.postTranslate(sx - enemyBitmap.width / 2f, sy - enemyBitmap.height / 2f)
            canvas.drawBitmap(enemyBitmap, matrix, null)
        } else {
            // Fallback: draw colored circle soldier
            healthPaint.color = android.graphics.Color.parseColor("#E53935")
            healthPaint.style = Paint.Style.FILL
            canvas.drawCircle(sx, sy, 38f, healthPaint)
            healthPaint.color = android.graphics.Color.parseColor("#B71C1C")
            healthPaint.style = Paint.Style.STROKE; healthPaint.strokeWidth = 4f
            canvas.drawCircle(sx, sy, 38f, healthPaint)
            healthPaint.style = Paint.Style.FILL
            // Direction indicator
            val rad = Math.toRadians(angle.toDouble())
            healthPaint.color = android.graphics.Color.WHITE
            canvas.drawCircle((sx + cos(rad) * 28f).toFloat(), (sy + sin(rad) * 28f).toFloat(), 8f, healthPaint)
        }

        // Health bar (always shown when damaged)
        if (health < 100) {
            healthPaint.color = android.graphics.Color.parseColor("#33FF0000")
            healthPaint.style = Paint.Style.FILL
            canvas.drawRect(sx - 42f, sy - 58f, sx + 42f, sy - 46f, healthPaint)
            healthPaint.color = android.graphics.Color.parseColor("#FF4444")
            canvas.drawRect(sx - 42f, sy - 58f, sx - 42f + (84f * health / 100f), sy - 46f, healthPaint)
        }
    }
}
