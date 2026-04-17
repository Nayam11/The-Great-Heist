package org.test.heist

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Rect
import java.util.Random

class TileMap(private val context: Context) {
    val tileSize = 128
    val mapWidth = 28
    val mapHeight = 18
    
    var grid = Array(mapHeight) { IntArray(mapWidth) }
    
    private var floorBmp: Bitmap? = null
    private var wallBmp: Bitmap? = null
    private var boxBmp: Bitmap? = null
    private var goldBmp: Bitmap? = null
    private var exitBmp: Bitmap? = null
    private var healthBmp: Bitmap? = null
    private var speedBmp: Bitmap? = null

    init {
        loadAssets()
    }

    private fun loadAssets() {
        try {
            floorBmp = loadScaledBitmap("PNG/Tiles/tile_01.png")
            wallBmp = loadScaledBitmap("PNG/Tiles/tile_11.png")
            boxBmp = loadScaledBitmap("box.png")
            goldBmp = loadScaledBitmap("gold.png")
            exitBmp = loadScaledBitmap("door.png")
            healthBmp = loadScaledBitmap("health_potion.png")
            speedBmp = loadScaledBitmap("speed_potion.png")
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun loadScaledBitmap(path: String): Bitmap {
        val inputStream = context.assets.open(path)
        val original = BitmapFactory.decodeStream(inputStream)
        val scaled = Bitmap.createScaledBitmap(original, tileSize, tileSize, true)
        if (scaled != original) original.recycle() // CRITICAL: RECYCLE original to save memory
        return scaled
    }

    fun generateLevel(level: Int) {
        val random = Random()
        grid = Array(mapHeight) { IntArray(mapWidth) { 0 } }

        // Single-tile border walls
        for (i in 0 until mapWidth) {
            grid[0][i] = 1; grid[mapHeight - 1][i] = 1
        }
        for (i in 0 until mapHeight) {
            grid[i][0] = 1; grid[i][mapWidth - 1] = 1
        }

        // Generate rooms (scaled to small map)
        val numRooms = minOf(10, 4 + level)
        for (i in 0 until numRooms) {
            val roomW = random.nextInt(5) + 4   // 4..8
            val roomH = random.nextInt(4) + 3   // 3..6
            val startX = random.nextInt(mapWidth  - roomW - 4) + 2
            val startY = random.nextInt(mapHeight - roomH - 4) + 2

            for (rx in 0 until roomW) {
                grid[startY][startX + rx] = 1
                grid[startY + roomH - 1][startX + rx] = 1
            }
            for (ry in 0 until roomH) {
                grid[startY + ry][startX] = 1
                grid[startY + ry][startX + roomW - 1] = 1
            }
            // Doorway
            grid[startY][startX + roomW / 2] = 0

            // Guaranteed potion inside every other room
            if (i % 2 == 0) {
                val px = startX + roomW / 2
                val py = startY + roomH / 2
                if (py in 1 until mapHeight - 1 && px in 1 until mapWidth - 1)
                    grid[py][px] = if (random.nextBoolean()) 5 else 6
            }
        }

        ensureConnected()

        // Gold count: 3-4 for level 1, +2 per level
        val goldCount = 3 + ((level - 1) * 2)
        var placed = 0
        var attempts = 0
        while (placed < goldCount && attempts < 2000) {
            attempts++
            val rx = random.nextInt(mapWidth - 4) + 2
            val ry = random.nextInt(mapHeight - 4) + 2
            if (grid[ry][rx] == 0) { grid[ry][rx] = 2; placed++ }
        }

        // Scatter boxes as obstacles (scaled)
        val boxCount = 3 + level
        placed = 0; attempts = 0
        while (placed < boxCount && attempts < 2000) {
            attempts++
            val rx = random.nextInt(mapWidth - 4) + 2
            val ry = random.nextInt(mapHeight - 4) + 2
            if (grid[ry][rx] == 0) { grid[ry][rx] = 4; placed++ }
        }

        // Extra potions scattered in open areas
        val potionCount = 2 + level
        placed = 0; attempts = 0
        while (placed < potionCount && attempts < 2000) {
            attempts++
            val rx = random.nextInt(mapWidth - 4) + 2
            val ry = random.nextInt(mapHeight - 4) + 2
            if (grid[ry][rx] == 0) {
                grid[ry][rx] = if (random.nextBoolean()) 5 else 6
                placed++
            }
        }

        // Exit door — place it far from player start (top-left area = player).
        // Door goes to bottom-right quadrant for easy navigation.
        var doorPlaced = false
        attempts = 0
        while (!doorPlaced && attempts < 2000) {
            attempts++
            val dx = random.nextInt(mapWidth / 2) + mapWidth / 2 - 2
            val dy = random.nextInt(mapHeight / 2) + mapHeight / 2 - 2
            if (dx in 1 until mapWidth - 1 && dy in 1 until mapHeight - 1 && grid[dy][dx] == 0) {
                grid[dy][dx] = 3
                doorPlaced = true
            }
        }
        // Fallback: force door into last clear cell found
        if (!doorPlaced) {
            outer@ for (r in mapHeight - 3 downTo 2) for (c in mapWidth - 3 downTo 2)
                if (grid[r][c] == 0) { grid[r][c] = 3; break@outer }
        }
    }

    private fun ensureConnected() {
        var startR = -1
        var startC = -1
        for (r in 1 until mapHeight - 1) {
            for (c in 1 until mapWidth - 1) {
                if (grid[r][c] == 0) {
                    startR = r; startC = c
                    break
                }
            }
            if (startR != -1) break
        }
        if (startR == -1) return

        val visited = mutableSetOf<Pair<Int, Int>>()
        val queue = mutableListOf<Pair<Int, Int>>()
        queue.add(Pair(startR, startC))
        visited.add(Pair(startR, startC))

        while (queue.isNotEmpty()) {
            val (r, c) = queue.removeAt(0)
            for ((dr, dc) in listOf(0 to 1, 0 to -1, 1 to 0, -1 to 0)) {
                val nr = r + dr; val nc = c + dc
                if (nr in 1 until mapHeight - 1 && nc in 1 until mapWidth - 1) {
                    if (grid[nr][nc] != 1 && !visited.contains(Pair(nr, nc))) {
                        visited.add(Pair(nr, nc))
                        queue.add(Pair(nr, nc))
                    }
                }
            }
        }

        // Bridge disconnected parts
        for (r in 1 until mapHeight - 1) {
            for (c in 1 until mapWidth - 1) {
                if (grid[r][c] != 1 && !visited.contains(Pair(r, c))) {
                    val target = visited.first()
                    var currR = r; var currC = c
                    while (currR != target.first || currC != target.second) {
                        if (currC != target.second) currC += if (target.second > currC) 1 else -1
                        else if (currR != target.first) currR += if (target.first > currR) 1 else -1
                        grid[currR][currC] = 0
                        visited.add(Pair(currR, currC))
                    }
                }
            }
        }
    }

    fun draw(canvas: Canvas?, cameraX: Float, cameraY: Float) {
        if (canvas == null) return
        val p = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG)
        val ts = tileSize.toFloat()
        val half = ts / 2f
        val qtr  = ts / 4f

        for (row in 0 until mapHeight) {
            for (col in 0 until mapWidth) {
                val tile = grid[row][col]
                val x = col * tileSize - cameraX
                val y = row * tileSize - cameraY

                // Frustum cull
                if (x < -tileSize || x > canvas.width + tileSize ||
                    y < -tileSize || y > canvas.height + tileSize) continue

                // ── Floor (always) ──
                p.style = android.graphics.Paint.Style.FILL
                if (floorBmp != null) {
                    canvas.drawBitmap(floorBmp!!, x, y, null)
                } else {
                    p.color = android.graphics.Color.parseColor("#1a1a2e")
                    canvas.drawRect(x, y, x + ts, y + ts, p)
                }

                when (tile) {
                    // ── Wall ──
                    1 -> {
                        if (wallBmp != null) canvas.drawBitmap(wallBmp!!, x, y, null)
                        else {
                            p.color = android.graphics.Color.parseColor("#4a4a5a")
                            canvas.drawRect(x, y, x + ts, y + ts, p)
                            p.color = android.graphics.Color.parseColor("#2a2a3a")
                            p.style = android.graphics.Paint.Style.STROKE; p.strokeWidth = 3f
                            canvas.drawRect(x + 2, y + 2, x + ts - 2, y + ts - 2, p)
                            p.style = android.graphics.Paint.Style.FILL
                        }
                    }
                    // ── Gold coin ── (ALWAYS drawn as yellow circle + star)
                    2 -> {
                        if (goldBmp != null && goldBmp!!.width > 4) canvas.drawBitmap(goldBmp!!, x, y, null)
                        p.color = android.graphics.Color.parseColor("#FFD700")
                        canvas.drawCircle(x + half, y + half, qtr + 4f, p)
                        p.color = android.graphics.Color.parseColor("#FFA000")
                        p.style = android.graphics.Paint.Style.STROKE; p.strokeWidth = 3f
                        canvas.drawCircle(x + half, y + half, qtr + 4f, p)
                        p.style = android.graphics.Paint.Style.FILL
                        p.color = android.graphics.Color.parseColor("#FFEB3B")
                        canvas.drawCircle(x + half - 5f, y + half - 5f, 6f, p)
                    }
                    // ── Exit door ── (ALWAYS drawn as cyan doorway arch)
                    3 -> {
                        if (exitBmp != null && exitBmp!!.width > 4) canvas.drawBitmap(exitBmp!!, x, y, null)
                        // Door frame
                        p.color = android.graphics.Color.parseColor("#00BCD4")
                        canvas.drawRect(x + qtr, y + qtr, x + ts - qtr, y + ts - 4f, p)
                        // Door inner
                        p.color = android.graphics.Color.parseColor("#004D60")
                        canvas.drawRect(x + qtr + 6f, y + qtr + 6f, x + ts - qtr - 6f, y + ts - 10f, p)
                        // Glowing outline
                        p.color = android.graphics.Color.parseColor("#00FFFF"); p.alpha = 200
                        p.style = android.graphics.Paint.Style.STROKE; p.strokeWidth = 5f
                        canvas.drawRect(x + qtr, y + qtr, x + ts - qtr, y + ts - 4f, p)
                        p.style = android.graphics.Paint.Style.FILL; p.alpha = 255
                        // EXIT label
                        p.textSize = 18f; p.color = android.graphics.Color.WHITE; p.isFakeBoldText = true
                        canvas.drawText("EXIT", x + half - 18f, y + half + 8f, p)
                    }
                    // ── Box / cover ── (ALWAYS drawn as dark brown crate)
                    4 -> {
                        if (boxBmp != null && boxBmp!!.width > 4) canvas.drawBitmap(boxBmp!!, x, y, null)
                        p.color = android.graphics.Color.parseColor("#5D4037")
                        canvas.drawRect(x + 8f, y + 8f, x + ts - 8f, y + ts - 8f, p)
                        p.color = android.graphics.Color.parseColor("#3E2723")
                        p.style = android.graphics.Paint.Style.STROKE; p.strokeWidth = 4f
                        canvas.drawRect(x + 8f, y + 8f, x + ts - 8f, y + ts - 8f, p)
                        // Cross line (crate style)
                        canvas.drawLine(x + 8f, y + half, x + ts - 8f, y + half, p)
                        canvas.drawLine(x + half, y + 8f, x + half, y + ts - 8f, p)
                        p.style = android.graphics.Paint.Style.FILL
                    }
                    // ── Health potion ── (ALWAYS drawn as red cross)
                    5 -> {
                        if (healthBmp != null && healthBmp!!.width > 4) canvas.drawBitmap(healthBmp!!, x, y, null)
                        // Background circle
                        p.color = android.graphics.Color.parseColor("#880000")
                        canvas.drawCircle(x + half, y + half, qtr + 8f, p)
                        // Red cross
                        p.color = android.graphics.Color.parseColor("#FF1744")
                        canvas.drawRect(x + half - 6f, y + half - 20f, x + half + 6f, y + half + 20f, p)
                        canvas.drawRect(x + half - 20f, y + half - 6f, x + half + 20f, y + half + 6f, p)
                        // Shine
                        p.color = android.graphics.Color.parseColor("#FF8A80"); p.alpha = 150
                        canvas.drawCircle(x + half - 8f, y + half - 8f, 6f, p); p.alpha = 255
                    }
                    // ── Speed potion ── (ALWAYS drawn as blue lightning bolt)
                    6 -> {
                        if (speedBmp != null && speedBmp!!.width > 4) canvas.drawBitmap(speedBmp!!, x, y, null)
                        p.color = android.graphics.Color.parseColor("#1565C0")
                        canvas.drawCircle(x + half, y + half, qtr + 8f, p)
                        // Lightning bolt
                        val path = android.graphics.Path()
                        path.moveTo(x + half + 8f,  y + half - 20f)
                        path.lineTo(x + half - 10f, y + half + 4f)
                        path.lineTo(x + half + 4f,  y + half + 4f)
                        path.lineTo(x + half - 8f,  y + half + 20f)
                        path.lineTo(x + half + 12f, y + half - 2f)
                        path.lineTo(x + half - 2f,  y + half - 2f)
                        path.close()
                        p.color = android.graphics.Color.parseColor("#40C4FF")
                        canvas.drawPath(path, p)
                    }
                }
            }
        }
    }
}
