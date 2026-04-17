package org.test.heist

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.util.AttributeSet
import android.view.SurfaceHolder
import android.view.SurfaceView
import kotlin.math.*

class GameView(context: Context, attrs: AttributeSet? = null) : SurfaceView(context, attrs), Runnable {

    private var running = false
    private var gameThread: Thread? = null
    private val surfaceHolder: SurfaceHolder = holder
    private var canvas: Canvas? = null
    private val paint = Paint()

    // Audio
    private var soundPool: android.media.SoundPool? = null
    private var soundShoot = 0
    private var soundKaching = 0
    private var soundHit = 0

    // World & Camera
    private val tileMap = TileMap(context)
    private var cameraX = 0f
    private var cameraY = 0f

    // Entities
    private var playerX = (2 * 128 + 64).toFloat()  // Start near top-left safe zone
    private var playerY = (2 * 128 + 64).toFloat()
    private var playerBitmap: Bitmap? = null
    private var playerAngle = 0f
    private var playerSpeed = 12f
    private var speedBoostTimer = 0

    // Combat & Level
    private var currentLevel = 1
    private val enemies = mutableListOf<Enemy>()
    private val bullets = mutableListOf<Bullet>()
    private var gameState = "playing" // "playing" | "WASTED" | "VICTORY"
    private var animFrame = 0         // typewriter frame counter

    // Stats
    private var health = 100
    private var gold = 0
    private var ammo = 5

    // Shooting cooldown
    private var shootTimer = 0
    private val shootCooldown = 10

    // Twin-Stick Joysticks — bases initialized in onSizeChanged for correct landscape layout
    private var lJoyBaseX = 0f
    private var lJoyBaseY = 0f
    private var lJoyInX = 0f
    private var lJoyInY = 0f

    private var rJoyBaseX = 0f
    private var rJoyBaseY = 0f
    private var rJoyInX = 0f
    private var rJoyInY = 0f
    private var joysticksInitialized = false

    private val joyRadius = 140f
    private val deadzone = 25f
    private var isLDown = false
    private var isRDown = false

    // Track door position for HUD arrow
    private var doorWorldX = 0f
    private var doorWorldY = 0f

    // Pre-allocated objects for GC relief
    private val matrix = Matrix()
    private val sharedPaint = Paint()

    // Shared Assets to prevent OOM
    private var bulletBmp: Bitmap? = null
    private var enemyBmp: Bitmap? = null

    init {
        loadAssets()
        loadAudio()
    }

    // ─── Asset Loading ──────────────────────────────────────────────────────────

    private fun loadAssets() {
        try {
            // Player gun sprite
            val pIn = context.assets.open("PNG/Hitman 1/hitman1_gun.png")
            val pOrig = BitmapFactory.decodeStream(pIn)
            playerBitmap = Bitmap.createScaledBitmap(pOrig, 110, 110, true)
            if (playerBitmap != pOrig) pOrig.recycle()

            // Shared bullet bitmap (re-used by every Bullet instance)
            val bIn = context.assets.open("bullet.png")
            val bOrig = BitmapFactory.decodeStream(bIn)
            bulletBmp = Bitmap.createScaledBitmap(bOrig, 30, 15, true)
            if (bulletBmp != bOrig) bOrig.recycle()

            // Shared enemy bitmap (re-used by every Enemy instance)
            val eIn = context.assets.open("PNG/Soldier 1/soldier1_gun.png")
            val eOrig = BitmapFactory.decodeStream(eIn)
            enemyBmp = Bitmap.createScaledBitmap(eOrig, 100, 100, true)
            if (enemyBmp != eOrig) eOrig.recycle()

        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun loadAudio() {
        val attrs = android.media.AudioAttributes.Builder()
            .setUsage(android.media.AudioAttributes.USAGE_GAME)
            .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()
        soundPool = android.media.SoundPool.Builder()
            .setMaxStreams(5)
            .setAudioAttributes(attrs)
            .build()
        try {
            soundShoot  = soundPool!!.load(context.assets.openFd("shoot.wav"),   1)
            soundKaching = soundPool!!.load(context.assets.openFd("kaching.wav"), 1)
            soundHit    = soundPool!!.load(context.assets.openFd("hit.wav"),      1)
        } catch (e: Exception) { e.printStackTrace() }
    }

    // ─── Lifecycle ──────────────────────────────────────────────────────────────
    // ─── Size Changed (fix joystick landscape init) ─────────────────────────────
    override fun onSizeChanged(w: Int, h: Int, oldW: Int, oldH: Int) {
        super.onSizeChanged(w, h, oldW, oldH)
        if (!joysticksInitialized && w > 0 && h > 0) {
            lJoyBaseX = w * 0.15f;  lJoyBaseY = h * 0.72f
            lJoyInX   = lJoyBaseX; lJoyInY   = lJoyBaseY
            rJoyBaseX = w * 0.85f;  rJoyBaseY = h * 0.72f
            rJoyInX   = rJoyBaseX; rJoyInY   = rJoyBaseY
            joysticksInitialized = true
        }
    }


    fun setLevel(level: Int) {
        currentLevel = level
        health = 100; gold = 0; ammo = 5 + (level * 2); gameState = "playing"
        tileMap.generateLevel(level)
        // Cache door position for HUD arrow
        doorWorldX = 0f; doorWorldY = 0f
        outer@ for (r in 0 until tileMap.mapHeight) for (c in 0 until tileMap.mapWidth)
            if (tileMap.grid[r][c] == 3) {
                doorWorldX = c * tileMap.tileSize + tileMap.tileSize / 2f
                doorWorldY = r * tileMap.tileSize + tileMap.tileSize / 2f
                break@outer
            }
        spawnEnemies()
    }

    fun resume() {
        running = true
        gameThread = Thread(this)
        gameThread?.start()
    }

    fun pause() {
        running = false
        try { gameThread?.join() } catch (e: InterruptedException) { e.printStackTrace() }
    }

    override fun run() {
        while (running) {
            if (!surfaceHolder.surface.isValid) continue
            update()
            draw()
            control()
        }
    }

    // ─── Spawn ──────────────────────────────────────────────────────────────────

    private fun spawnEnemies() {
        enemies.clear()
        val rng = java.util.Random()
        val count = minOf(18, 5 + (currentLevel * 1.5).toInt())
        var spawned = 0
        var attempts = 0
        while (spawned < count && attempts < 5000) {
            attempts++
            val gx = rng.nextInt(tileMap.mapWidth)
            val gy = rng.nextInt(tileMap.mapHeight)
            if (tileMap.grid[gy][gx] == 0) {
                val ex = gx * tileMap.tileSize.toFloat() + tileMap.tileSize / 2f
                val ey = gy * tileMap.tileSize.toFloat() + tileMap.tileSize / 2f
                val dist = sqrt((ex - playerX).pow(2) + (ey - playerY).pow(2))
                if (dist > 500f) {
                    enemies.add(Enemy(context, ex, ey, enemyBmp).apply { setLevel(currentLevel) })
                    spawned++
                }
            }
        }
    }

    // ─── Collision helpers ────────────────────────────────────────────────────────

    /** 4-corner AABB collision for the player (radius = 28px). */
    private fun canPlayerMove(nx: Float, ny: Float): Boolean {
        val r = 28f
        val ts = tileMap.tileSize
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

    // ─── Update ─────────────────────────────────────────────────────────────────

    private fun update() {
        if (gameState == "WASTED" || gameState == "VICTORY") return

        health = maxOf(0, minOf(100, health))
        if (health <= 0) {
            gameState = "WASTED"; animFrame = 0
            soundPool?.play(soundHit, 1f, 1f, 0, 0, 0.5f)
            return
        }

        cameraX = playerX - width  / 2f
        cameraY = playerY - height / 2f

        // Speed boost
        if (speedBoostTimer > 0) { speedBoostTimer--; playerSpeed = 22f } else playerSpeed = 12f

        // Gold / mission status
        var remainingGold = 0
        for (r in 0 until tileMap.mapHeight) for (c in 0 until tileMap.mapWidth) if (tileMap.grid[r][c] == 2) remainingGold++
        val allSecured = remainingGold == 0 && enemies.isEmpty()

        // ── Player movement (Left stick) — also drives facing when not aiming ──
        if (isLDown) {
            val dx = lJoyInX - lJoyBaseX
            val dy = lJoyInY - lJoyBaseY
            val dist = sqrt(dx * dx + dy * dy)
            if (dist > deadzone) {
                if (!isRDown) {
                    playerAngle = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble())).toFloat()
                }
                val nd = dist.coerceAtMost(joyRadius)
                val nx = playerX + (dx / dist) * playerSpeed
                val ny = playerY + (dy / dist) * playerSpeed

                // Try full move, then axis-slide (prevents sticking on corners)
                when {
                    canPlayerMove(nx, ny) -> { playerX = nx; playerY = ny }
                    canPlayerMove(nx, playerY) -> { playerX = nx }
                    canPlayerMove(playerX, ny) -> { playerY = ny }
                }

                // Pickup / interaction at current tile
                val gx = (playerX / tileMap.tileSize).toInt()
                val gy = (playerY / tileMap.tileSize).toInt()
                if (gx in 0 until tileMap.mapWidth && gy in 0 until tileMap.mapHeight) {
                    when (tileMap.grid[gy][gx]) {
                        2 -> { tileMap.grid[gy][gx] = 0; gold += 100; ammo += 2; soundPool?.play(soundKaching, 1f, 1f, 0, 0, 1f) }
                        5 -> { tileMap.grid[gy][gx] = 0; health = minOf(100, health + 20); soundPool?.play(soundKaching, 1f, 1f, 0, 0, 1.2f) }
                        6 -> { tileMap.grid[gy][gx] = 0; speedBoostTimer = 300; soundPool?.play(soundKaching, 1f, 1f, 0, 0, 1.3f) }
                        3 -> if (allSecured) {
                            // Keep running=true so the draw loop renders the VICTORY screen
                            gameState = "VICTORY"; animFrame = 0
                            val prefs = context.getSharedPreferences("HEIST_SAVE", android.content.Context.MODE_PRIVATE)
                            val unlocked = prefs.getInt("UNLOCKED_LEVEL", 1)
                            if (currentLevel >= unlocked) prefs.edit().putInt("UNLOCKED_LEVEL", currentLevel + 1).apply()
                        }
                    }
                }
            }
        }

        // ── Aiming & Shooting (Right stick) ──
        if (isRDown) {
            val dx = rJoyInX - rJoyBaseX
            val dy = rJoyInY - rJoyBaseY
            val angle = atan2(dy.toDouble(), dx.toDouble()).toFloat()
            playerAngle = Math.toDegrees(angle.toDouble()).toFloat()

            shootTimer++
            if (shootTimer >= shootCooldown && ammo > 0) {
                shootTimer = 0; ammo--
                val tx = playerX + cos(angle) * 100
                val ty = playerY + sin(angle) * 100
                bullets.add(Bullet(context, playerX, playerY, tx, ty, "player", bulletBmp))
                soundPool?.play(soundShoot, 0.7f, 0.7f, 0, 0, 1f)
            }
        } else {
            shootTimer = shootCooldown
        }

        // ── Bullet update — wall LOS kill ──
        val deadBullets = mutableSetOf<Bullet>()
        for (b in bullets) {
            b.update()
            if (b.isDead()) { deadBullets.add(b); continue }

            val bx = (b.x / tileMap.tileSize).toInt()
            val by = (b.y / tileMap.tileSize).toInt()
            if (bx in 0 until tileMap.mapWidth && by in 0 until tileMap.mapHeight) {
                if (tileMap.grid[by][bx] == 1 || tileMap.grid[by][bx] == 4) { deadBullets.add(b); continue }
            }

            if (b.owner == "player" && !deadBullets.contains(b)) {
                for (e in enemies) {
                    if (sqrt((b.x - e.x).pow(2) + (b.y - e.y).pow(2)) < 55f) {
                        e.health -= b.damage
                        deadBullets.add(b)
                        soundPool?.play(soundHit, 0.5f, 0.5f, 0, 0, 1f)
                        if (e.health <= 0) {
                            // Cache death position BEFORE removing from list
                            val deadX = e.x; val deadY = e.y
                            // Mark for removal
                            val deadEnemy = e
                            // Alert the closest ALIVE survivor (excluding the dead one)
                            enemies
                                .filter { it !== deadEnemy && it.health > 0 }
                                .minByOrNull { sqrt((it.x - deadX).pow(2) + (it.y - deadY).pow(2)) }
                                ?.investigate(deadX, deadY)
                        }
                        break
                    }
                }
            } else if (b.owner == "enemy" && !deadBullets.contains(b)) {
                if (sqrt((b.x - playerX).pow(2) + (b.y - playerY).pow(2)) < 45f) {
                    health -= b.damage
                    deadBullets.add(b)
                    soundPool?.play(soundHit, 0.8f, 0.8f, 0, 0, 0.8f)
                }
            }
        }
        enemies.removeAll { it.health <= 0 }.also { if (it) ammo += 5 }
        bullets.removeAll(deadBullets)

        // ── Enemy update ──
        enemies.forEach { e ->
            e.update(playerX, playerY, tileMap, bulletBmp)?.let { bullets.add(it) }
        }
    }

    // ─── Draw ───────────────────────────────────────────────────────────────────

    private fun draw() {
        canvas = surfaceHolder.lockCanvas() ?: return
        canvas!!.let { c ->
            c.drawColor(Color.parseColor("#0a0a0a"))
            tileMap.draw(c, cameraX, cameraY)
            for (e in enemies) e.draw(c, cameraX, cameraY)
            for (b in bullets) b.draw(c, cameraX, cameraY)

            // Crosshair
            if (isRDown) {
                sharedPaint.color = Color.RED; sharedPaint.alpha = 160; sharedPaint.style = Paint.Style.FILL
                val cX = playerX - cameraX + (rJoyInX - rJoyBaseX) * 3
                val cY = playerY - cameraY + (rJoyInY - rJoyBaseY) * 3
                c.drawCircle(cX, cY, 18f, sharedPaint)
            }

            // Player — face the aiming/movement direction
            playerBitmap?.let { bmp ->
                matrix.reset()
                // hitman1_gun.png faces RIGHT by default in asset pack
                // playerAngle: 0=right, 90=down (atan2 convention) — no offset needed
                matrix.postRotate(playerAngle, bmp.width / 2f, bmp.height / 2f)
                matrix.postTranslate(playerX - cameraX - bmp.width / 2f, playerY - cameraY - bmp.height / 2f)
                c.drawBitmap(bmp, matrix, null)
            }

            drawUI(c)
            surfaceHolder.unlockCanvasAndPost(c)
        }
    }

    private fun drawUI(canvas: Canvas) {
        val uiH = 160f

        // Gold count for HUD
        var remainingGold = 0
        for (r in 0 until tileMap.mapHeight) for (col in 0 until tileMap.mapWidth) if (tileMap.grid[r][col] == 2) remainingGold++

        // Dashboard background
        paint.style = Paint.Style.FILL
        paint.color = Color.BLACK; paint.alpha = 170
        canvas.drawRect(0f, 0f, width.toFloat(), uiH, paint)
        paint.color = Color.parseColor("#FFD700"); paint.alpha = 220
        canvas.drawRect(0f, uiH - 3f, width.toFloat(), uiH, paint)

        // 1. Vitality bar (left)
        paint.alpha = 255; paint.color = Color.WHITE; paint.textSize = 24f; paint.isFakeBoldText = true
        canvas.drawText("HEALTH", 50f, 45f, paint)
        paint.color = Color.DKGRAY; paint.alpha = 130
        canvas.drawRect(50f, 60f, 380f, 95f, paint)
        paint.color = if (health > 30) Color.parseColor("#2ECC71") else Color.parseColor("#E74C3C"); paint.alpha = 255
        canvas.drawRect(50f, 60f, 50f + health * 3.3f, 95f, paint)
        paint.textSize = 22f; paint.color = Color.WHITE
        canvas.drawText("${health}%", 390f, 90f, paint)

        // 2. Centre — gold coins collected (no dollar sign)
        paint.color = Color.parseColor("#FFD700"); paint.textSize = 48f
        val goldStr = "$gold"
        canvas.drawText(goldStr, width / 2f - paint.measureText(goldStr) / 2f, 85f, paint)
        paint.textSize = 16f; paint.color = Color.LTGRAY
        canvas.drawText("GOLD", width / 2f - paint.measureText("GOLD") / 2f, 115f, paint)

        // 3. Intel (right)
        paint.color = Color.WHITE; paint.textSize = 28f; paint.alpha = 255
        canvas.drawText("FOES:${enemies.size}", width - 540f, 75f, paint)
        canvas.drawText("LOOT:$remainingGold", width - 370f, 75f, paint)
        canvas.drawText("AMMO:$ammo",          width - 200f, 75f, paint)

        // 4. Door direction arrow (always visible compass)
        if (doorWorldX > 0f || doorWorldY > 0f) {
            val dx = doorWorldX - playerX
            val dy = doorWorldY - playerY
            val dist = sqrt(dx * dx + dy * dy)
            val arrowAngle = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble())).toFloat()
            val cx = width - 80f; val cy = uiH / 2f
            // Circle
            paint.color = Color.parseColor("#FFD700"); paint.alpha = 200; paint.style = Paint.Style.STROKE; paint.strokeWidth = 4f
            canvas.drawCircle(cx, cy, 38f, paint)
            // Arrow pointing to door
            paint.style = Paint.Style.FILL; paint.alpha = 255
            val rad = Math.toRadians(arrowAngle.toDouble())
            val tx = cx + (cos(rad) * 28).toFloat(); val ty = cy + (sin(rad) * 28).toFloat()
            val p = android.graphics.Path()
            val perpRad = rad + Math.PI / 2
            p.moveTo(tx, ty)
            p.lineTo((cx + cos(perpRad) * 10).toFloat(), (cy + sin(perpRad) * 10).toFloat())
            p.lineTo((cx - cos(perpRad) * 10).toFloat(), (cy - sin(perpRad) * 10).toFloat())
            p.close()
            canvas.drawPath(p, paint)
            // Distance in tiles
            paint.textSize = 16f; paint.color = Color.WHITE; paint.style = Paint.Style.FILL
            val distTiles = (dist / tileMap.tileSize).toInt()
            val distStr = "${distTiles}m"
            canvas.drawText(distStr, cx - paint.measureText(distStr) / 2f, cy + 56f, paint)
            // Label
            paint.textSize = 12f; paint.color = Color.parseColor("#FFD700")
            canvas.drawText("EXIT", cx - paint.measureText("EXIT") / 2f, cy - 48f, paint)
        }
        paint.strokeWidth = 1f; paint.style = Paint.Style.FILL

        // 5. Joystick indicators — outer ring + knob with higher visibility
        paint.style = Paint.Style.STROKE; paint.strokeWidth = 4f
        paint.color = Color.parseColor("#AAAAAA"); paint.alpha = 100
        canvas.drawCircle(lJoyBaseX, lJoyBaseY, joyRadius, paint)
        canvas.drawCircle(rJoyBaseX, rJoyBaseY, joyRadius, paint)
        paint.style = Paint.Style.FILL; paint.strokeWidth = 1f
        paint.color = Color.parseColor("#555555"); paint.alpha = 60
        canvas.drawCircle(lJoyBaseX, lJoyBaseY, joyRadius, paint)
        canvas.drawCircle(rJoyBaseX, rJoyBaseY, joyRadius, paint)
        paint.color = Color.parseColor("#FFD700"); paint.alpha = 130
        canvas.drawCircle(lJoyInX, lJoyInY, 58f, paint)
        paint.color = Color.RED; paint.alpha = 130
        canvas.drawCircle(rJoyInX, rJoyInY, 58f, paint)

        // 6. WASTED overlay — typewriter pixel animation
        if (gameState == "WASTED") {
            animFrame++
            paint.color = android.graphics.Color.BLACK; paint.alpha = 255
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), paint)

            val fullMsg = "WASTED"
            val lettersToShow = minOf(fullMsg.length, animFrame / 3)
            val visibleMsg = fullMsg.substring(0, lettersToShow)
            val cursor = if (lettersToShow < fullMsg.length || (animFrame / 15) % 2 == 0) "_" else ""

            paint.textSize = 140f; paint.isFakeBoldText = true; paint.alpha = 255
            val ty = height / 2f

            // Shadow
            paint.color = android.graphics.Color.parseColor("#880000")
            val sw = paint.measureText(visibleMsg + cursor)
            canvas.drawText(visibleMsg + cursor, width / 2f - sw / 2f + 6f, ty + 6f, paint)
            // Main text
            paint.color = android.graphics.Color.RED
            canvas.drawText(visibleMsg + cursor, width / 2f - paint.measureText(visibleMsg + cursor) / 2f, ty, paint)

            // Subtitle — appears only after main text finishes
            if (lettersToShow >= fullMsg.length) {
                val sub = "TAP TO RETREAT"
                val subAlpha = minOf(255, (animFrame - fullMsg.length * 3) * 8)
                paint.textSize = 36f; paint.color = android.graphics.Color.parseColor("#AAAAAA"); paint.alpha = subAlpha
                canvas.drawText(sub, width / 2f - paint.measureText(sub) / 2f, ty + 110f, paint)
            }
            paint.alpha = 255
        }

        // 7. VICTORY overlay — typewriter gold animation
        if (gameState == "VICTORY") {
            animFrame++
            paint.color = android.graphics.Color.BLACK; paint.alpha = 255
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), paint)

            val fullMsg = "MISSION CLEAR"
            val lettersToShow = minOf(fullMsg.length, animFrame / 3)
            val visibleMsg = fullMsg.substring(0, lettersToShow)
            val cursor = if (lettersToShow < fullMsg.length || (animFrame / 15) % 2 == 0) "_" else ""

            paint.textSize = 110f; paint.isFakeBoldText = true; paint.alpha = 255
            val vy = height / 2f - 40f

            // Shadow
            paint.color = android.graphics.Color.parseColor("#7B6000")
            canvas.drawText(visibleMsg + cursor, width / 2f - paint.measureText(visibleMsg + cursor) / 2f + 6f, vy + 6f, paint)
            // Main text
            paint.color = android.graphics.Color.parseColor("#FFD700")
            canvas.drawText(visibleMsg + cursor, width / 2f - paint.measureText(visibleMsg + cursor) / 2f, vy, paint)

            if (lettersToShow >= fullMsg.length) {
                val subAlpha = minOf(255, (animFrame - fullMsg.length * 3) * 8)

                // Gold count typewriter line 2
                val gs = "ASSETS SECURED: $gold"
                val gs2Show = minOf(gs.length, (animFrame - fullMsg.length * 3) / 2)
                paint.textSize = 50f; paint.color = android.graphics.Color.WHITE; paint.alpha = subAlpha
                val gsSub = gs.substring(0, gs2Show)
                canvas.drawText(gsSub, width / 2f - paint.measureText(gsSub) / 2f, vy + 110f, paint)

                // Tap to continue
                paint.textSize = 32f; paint.color = android.graphics.Color.parseColor("#AAAAAA"); paint.alpha = subAlpha
                val vsub = "TAP TO CONTINUE"
                canvas.drawText(vsub, width / 2f - paint.measureText(vsub) / 2f, vy + 190f, paint)

                // AUBLIQUE branding
                paint.textSize = 18f; paint.color = android.graphics.Color.parseColor("#CDFF00"); paint.alpha = subAlpha / 2
                val brand = "✦  AN  AUBLIQUE  EXPERIENCE  ✦"
                canvas.drawText(brand, width / 2f - paint.measureText(brand) / 2f, vy + 260f, paint)
            }
            paint.alpha = 255
        }
    }

    // ─── Touch ──────────────────────────────────────────────────────────────────

    override fun onTouchEvent(event: android.view.MotionEvent): Boolean {
        if (gameState == "WASTED") {
            if (event.action == android.view.MotionEvent.ACTION_DOWN)
                (context as? android.app.Activity)?.finish()
            return true
        }
        if (gameState == "VICTORY") {
            if (event.action == android.view.MotionEvent.ACTION_DOWN)
                (context as? android.app.Activity)?.finish()
            return true
        }

        val pi = event.actionIndex
        val x  = event.getX(pi)
        val y  = event.getY(pi)

        when (event.actionMasked) {
            android.view.MotionEvent.ACTION_DOWN, android.view.MotionEvent.ACTION_POINTER_DOWN -> {
                if (x < width / 2) { isLDown = true;  lJoyInX = x; lJoyInY = y; lJoyBaseX = x; lJoyBaseY = y }
                else               { isRDown = true;  rJoyInX = x; rJoyInY = y; rJoyBaseX = x; rJoyBaseY = y }
            }
            android.view.MotionEvent.ACTION_MOVE -> {
                for (i in 0 until event.pointerCount) {
                    val px = event.getX(i); val py = event.getY(i)
                    if (px < width / 2) { lJoyInX = px; lJoyInY = py } else { rJoyInX = px; rJoyInY = py }
                }
            }
            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_POINTER_UP -> {
                if (x < width / 2) { isLDown = false; lJoyInX = lJoyBaseX; lJoyInY = lJoyBaseY }
                else               { isRDown = false; rJoyInX = rJoyBaseX; rJoyInY = rJoyBaseY }
            }
        }
        return true
    }

    // ─── Control ────────────────────────────────────────────────────────────────

    private fun control() {
        try { Thread.sleep(17) } catch (e: InterruptedException) { e.printStackTrace() }
    }
}
